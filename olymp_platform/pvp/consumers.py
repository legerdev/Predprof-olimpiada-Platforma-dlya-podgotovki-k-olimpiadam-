import json
import asyncio
from datetime import timedelta

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from django.utils import timezone

from .models import Match
from .elo import update_elo
from problems.utils import normalize_answer

GRACE_SECONDS = 8


class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = int(self.scope["url_route"]["kwargs"]["match_id"])
        self.group_name = f"match_{self.match_id}"
        self.user = self.scope["user"]

        self._timer_task = None
        self._dc_task = None

        if not self.user.is_authenticated:
            await self.close(code=4000)
            return

        match = await self.get_match_related()
        if self.user.id not in [match.player1_id, match.player2_id]:
            await self.close(code=4000)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.set_presence(is_connected=True)

        match = await self.maybe_start_match_if_ready()

        await self.send(json.dumps(self._state(match)))
        await self.broadcast_state(match)

        await self.maybe_start_timer(match)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

        await self.set_presence(is_connected=False)

        match = await self.get_match_related()
        await self.broadcast_state(match)

        if match.status == Match.Status.ACTIVE and match.started_at and match.player2_id:
            if self._dc_task:
                self._dc_task.cancel()
            self._dc_task = asyncio.create_task(self.delayed_technical_check())

    async def delayed_technical_check(self):
        try:
            await asyncio.sleep(GRACE_SECONDS)
            payload = await self.mark_technical_if_still_disconnected()
            if payload:
                await self.channel_layer.group_send(
                    self.group_name,
                    {"type": "match_state", "payload": payload}
                )
        except asyncio.CancelledError:
            return

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "submit_answer":
            answer = (data.get("answer") or "").strip()
            if not answer:
                return

            match = await self.get_match_related()
            if match.status != Match.Status.ACTIVE or not match.started_at or not match.expires_at:
                return

            await self.finish_by_timeout_if_needed()

            res = await self.apply_answer(answer)
            if not res:
                return

            if res.get("my_correct") is True:
                await self.send(json.dumps({"type": "toast", "level": "success", "message": "✅ Правильно!"}))
            elif res.get("my_correct") is False:
                await self.send(json.dumps({"type": "toast", "level": "error", "message": "❌ Неправильно"}))


            await self.channel_layer.group_send(
                self.group_name,
                {"type": "match_state", "payload": res["state"]}
            )

            if res["should_finish_now"]:
                await self.finish_draw_now()

            await self.maybe_start_timer(await self.get_match_related())

    async def match_state(self, event):
        await self.send(json.dumps(event["payload"]))


    def _state(self, match: Match):
        return {
            "type": "state",
            "match_id": match.id,
            "status": match.status,
            "result": match.result,
            "started_at": match.started_at.isoformat() if match.started_at else None,
            "expires_at": match.expires_at.isoformat() if match.expires_at else None,
            "p1": {
                "username": match.player1.username if match.player1_id else None,
                "score": match.p1_score,
                "state": match.p1_state,
            },
            "p2": {
                "username": match.player2.username if match.player2_id else None,
                "score": match.p2_score,
                "state": match.p2_state,
            },
            "problem": {
                "title": match.problem.title if match.problem_id else None,
                "text": match.problem.text if match.problem_id else None,
            },
        }

    async def broadcast_state(self, match: Match):
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "match_state", "payload": self._state(match)}
        )


    @database_sync_to_async
    def get_match_related(self):
        return Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)


    @database_sync_to_async
    def set_presence(self, is_connected: bool):
        field_names = {f.name for f in Match._meta.fields}
        needed = {"p1_connected", "p2_connected", "p1_disconnected_at", "p2_disconnected_at"}
        if not needed.issubset(field_names):
            return

        with transaction.atomic():
            m = Match.objects.select_for_update().get(id=self.match_id)
            if m.status not in [Match.Status.WAITING, Match.Status.ACTIVE]:
                return

            now = timezone.now()
            is_p1 = (self.user.id == m.player1_id)

            if is_p1:
                m.p1_connected = is_connected
                m.p1_disconnected_at = None if is_connected else now
            else:
                m.p2_connected = is_connected
                m.p2_disconnected_at = None if is_connected else now

            m.save(update_fields=["p1_connected", "p2_connected", "p1_disconnected_at", "p2_disconnected_at"])


    @database_sync_to_async
    def maybe_start_match_if_ready(self):
        """
        FIX: нельзя делать select_for_update + select_related на nullable FK (player2/problem).
        Поэтому:
        1) лочим только match-строку без join
        2) обновляем started_at/expires_at
        3) перечитываем с select_related для state
        """
        with transaction.atomic():
            m = Match.objects.select_for_update().get(id=self.match_id)

            if m.status != Match.Status.ACTIVE:
                return Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)

            if not m.player2_id:
                return Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)

            field_names = {f.name for f in Match._meta.fields}
            has_presence = {"p1_connected", "p2_connected"}.issubset(field_names)

            ready = True
            if has_presence:
                ready = bool(m.p1_connected and m.p2_connected)

            if m.started_at is None and ready:
                now = timezone.now()
                m.started_at = now
                dur = getattr(m, "duration_sec", 90) or 90
                m.expires_at = now + timedelta(seconds=dur)
                m.save(update_fields=["started_at", "expires_at"])

        return Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)


    @database_sync_to_async
    def mark_technical_if_still_disconnected(self):
        field_names = {f.name for f in Match._meta.fields}
        needed = {"p1_connected", "p2_connected", "p1_disconnected_at", "p2_disconnected_at"}
        if not needed.issubset(field_names):
            return None

        with transaction.atomic():
            m = Match.objects.select_for_update().get(id=self.match_id)

            if m.status != Match.Status.ACTIVE:
                return None
            if not m.player2_id:
                return None
            if not m.started_at:
                return None

            now = timezone.now()
            is_p1 = (self.user.id == m.player1_id)

            if is_p1:
                if m.p1_connected:
                    return None
                if not m.p1_disconnected_at or (now - m.p1_disconnected_at).total_seconds() < GRACE_SECONDS:
                    return None
            else:
                if m.p2_connected:
                    return None
                if not m.p2_disconnected_at or (now - m.p2_disconnected_at).total_seconds() < GRACE_SECONDS:
                    return None

            m.status = Match.Status.TECHNICAL
            m.result = Match.Result.TECHNICAL
            m.ended_at = timezone.now()
            m.winner = None
            m.save(update_fields=["status", "result", "ended_at", "winner"])

        m = Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)
        return self._state(m)


    async def maybe_start_timer(self, match: Match):
        if match.status != Match.Status.ACTIVE or not match.expires_at:
            return
        if self._timer_task:
            return

        seconds = (match.expires_at - timezone.now()).total_seconds()
        if seconds <= 0:
            await self.finish_by_timeout_if_needed()
            return

        async def _sleep_and_finish():
            try:
                await asyncio.sleep(seconds)
                await self.finish_by_timeout_if_needed()
            except asyncio.CancelledError:
                return

        self._timer_task = asyncio.create_task(_sleep_and_finish())

    async def finish_by_timeout_if_needed(self):
        payload = await self.finish_match_if_expired()
        if payload:
            await self.channel_layer.group_send(self.group_name, {"type": "match_state", "payload": payload})


    @database_sync_to_async
    def apply_answer(self, answer: str):
        with transaction.atomic():
            match = Match.objects.select_for_update().get(id=self.match_id)

            if match.status != Match.Status.ACTIVE or not match.problem_id:
                return None
            if not match.started_at or not match.expires_at:
                return None
            if timezone.now() >= match.expires_at:
                s = Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)
                return {"state": self._state(s), "should_finish_now": False, "my_correct": None}

            prob = match.problem
            correct = normalize_answer(answer) == normalize_answer(prob.correct_answer)
            is_p1 = (self.user.id == match.player1_id)

            if not match.allow_resubmit:
                if is_p1 and match.p1_last_submit_at is not None:
                    s = Match.objects.select_related("player1","player2","problem").get(id=self.match_id)
                    return {"state": self._state(s), "should_finish_now": False, "my_correct": None}
                if (not is_p1) and match.p2_last_submit_at is not None:
                    s = Match.objects.select_related("player1","player2","problem").get(id=self.match_id)
                    return {"state": self._state(s), "should_finish_now": False, "my_correct": None}

            now = timezone.now()
            if is_p1:
                match.p1_last_answer = answer
                match.p1_last_submit_at = now
                match.p1_state = Match.AnswerState.CORRECT if correct else Match.AnswerState.WRONG
                match.p1_score = 1 if correct else 0
            else:
                match.p2_last_answer = answer
                match.p2_last_submit_at = now
                match.p2_state = Match.AnswerState.CORRECT if correct else Match.AnswerState.WRONG
                match.p2_score = 1 if correct else 0

            match.save()

        s = Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)
        should_finish_now = (s.p1_score == 1 and s.p2_score == 1)
        return {"state": self._state(s), "should_finish_now": should_finish_now, "my_correct": correct}



    @database_sync_to_async
    def finish_match_if_expired(self):
        with transaction.atomic():
            match = Match.objects.select_for_update().get(id=self.match_id)
            if match.status != Match.Status.ACTIVE or not match.expires_at or not match.started_at:
                return None
            if timezone.now() < match.expires_at:
                return None

            if match.p1_score > match.p2_score:
                result = Match.Result.P1_WIN
                s1 = 1.0
            elif match.p2_score > match.p1_score:
                result = Match.Result.P2_WIN
                s1 = 0.0
            else:
                result = Match.Result.DRAW
                s1 = 0.5

            p1 = match.player1
            p2 = match.player2

            match.p1_rating_before = p1.rating
            match.p2_rating_before = p2.rating

            r1, r2 = update_elo(p1.rating, p2.rating, s1, k=32)
            p1.rating = r1
            p2.rating = r2
            p1.save()
            p2.save()

            match.p1_rating_after = r1
            match.p2_rating_after = r2

            match.status = Match.Status.FINISHED
            match.result = result
            match.ended_at = timezone.now()
            match.winner = p1 if result == Match.Result.P1_WIN else p2 if result == Match.Result.P2_WIN else None
            match.save()

        s = Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)
        return self._state(s)

    async def finish_draw_now(self):
        payload = await self.finish_draw_sync()
        if payload:
            await self.channel_layer.group_send(self.group_name, {"type": "match_state", "payload": payload})

    @database_sync_to_async
    def finish_draw_sync(self):
        with transaction.atomic():
            match = Match.objects.select_for_update().get(id=self.match_id)
            if match.status != Match.Status.ACTIVE:
                return None

            p1 = match.player1
            p2 = match.player2

            match.p1_rating_before = p1.rating
            match.p2_rating_before = p2.rating

            r1, r2 = update_elo(p1.rating, p2.rating, 0.5, k=32)
            p1.rating = r1
            p2.rating = r2
            p1.save()
            p2.save()

            match.p1_rating_after = r1
            match.p2_rating_after = r2

            match.status = Match.Status.FINISHED
            match.result = Match.Result.DRAW
            match.ended_at = timezone.now()
            match.winner = None
            match.save()

        s = Match.objects.select_related("player1", "player2", "problem").get(id=self.match_id)
        return self._state(s)
