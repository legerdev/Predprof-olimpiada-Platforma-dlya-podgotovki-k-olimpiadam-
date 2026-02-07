import random
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, F
from django.db.models.functions import Abs
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Match
from .elo import update_elo
from problems.models import Problem


def _state_dict(match: Match) -> dict:
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


def _broadcast_state(match_id: int):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    m = Match.objects.select_related("player1", "player2", "problem").get(id=match_id)
    async_to_sync(channel_layer.group_send)(
        f"match_{m.id}",
        {"type": "match_state", "payload": _state_dict(m)}
    )


def pick_problem_for_pvp(p1, p2, avoid_last=30):
    """Не даём постоянно одну и ту же задачу: избегаем последних N у обоих игроков."""
    recent_ids = list(
        Match.objects.filter(
            Q(player1=p1) | Q(player2=p1) | Q(player1=p2) | Q(player2=p2),
            problem__isnull=False,
        )
        .order_by("-created_at")
        .values_list("problem_id", flat=True)[:avoid_last]
    )

    qs = Problem.objects.all()
    if hasattr(Problem, "is_active"):
        qs = qs.filter(is_active=True)

    if recent_ids:
        qs2 = qs.exclude(id__in=recent_ids)
        if qs2.exists():
            qs = qs2

    return qs.order_by("?").first()


@login_required
def pvp_hub(request):
    qs = (
        Match.objects
        .filter(Q(player1=request.user) | Q(player2=request.user))
        .select_related("player1", "player2")
        .order_by("-created_at")[:20]
    )

    history = []
    for m in qs:
        is_p1 = (m.player1_id == request.user.id)
        opponent = m.player2 if is_p1 else m.player1

        outcome = "—"
        if m.status == Match.Status.FINISHED and m.result:
            if m.result == Match.Result.DRAW:
                outcome = "D"
            elif m.result == Match.Result.P1_WIN:
                outcome = "W" if is_p1 else "L"
            elif m.result == Match.Result.P2_WIN:
                outcome = "W" if (not is_p1) else "L"
        elif m.status == Match.Status.CANCELLED:
            outcome = "C"
        elif m.status == Match.Status.TECHNICAL:
            outcome = "T"

        before = m.p1_rating_before if is_p1 else m.p2_rating_before
        after = m.p1_rating_after if is_p1 else m.p2_rating_after
        elo_delta = None
        if before is not None and after is not None and outcome not in ("C", "T"):
            elo_delta = int(after - before)

        history.append({
            "match": m,
            "opponent": opponent,
            "outcome": outcome,
            "elo_delta": elo_delta,
        })

    waiting = Match.objects.filter(status=Match.Status.WAITING, player1=request.user).first()

    elo_series = []
    finished = (
        Match.objects
        .filter(Q(player1=request.user) | Q(player2=request.user), status=Match.Status.FINISHED)
        .order_by("ended_at", "id")
        .only("id", "player1_id", "p1_rating_after", "p2_rating_after")
    )
    for m in finished:
        rating = m.p1_rating_after if m.player1_id == request.user.id else m.p2_rating_after
        if rating is not None:
            elo_series.append(int(rating))
    elo_series = elo_series[-50:]

    return render(request, "pvp_hub.html", {
        "history": history,
        "waiting": waiting,
        "elo_series": elo_series,
    })


@login_required
def pvp_start_queue(request):
    existing = Match.objects.filter(status=Match.Status.WAITING, player1=request.user).first()
    if existing:
        return redirect("pvp_match", match_id=existing.id)

    with transaction.atomic():
        candidate = (
            Match.objects
            .select_for_update(skip_locked=True)
            .filter(status=Match.Status.WAITING, player2__isnull=True)
            .exclude(player1=request.user)
            .annotate(diff=Abs(F("player1__rating") - request.user.rating))
            .order_by("diff", "created_at")
            .first()
        )

        if candidate:
            candidate.player2 = request.user
            candidate.status = Match.Status.ACTIVE

            candidate.started_at = None
            candidate.expires_at = None

            candidate.problem = pick_problem_for_pvp(candidate.player1, candidate.player2)

            candidate.p1_state = Match.AnswerState.IDLE
            candidate.p2_state = Match.AnswerState.IDLE
            candidate.p1_score = 0
            candidate.p2_score = 0
            candidate.save()

            _broadcast_state(candidate.id)
            return redirect("pvp_match", match_id=candidate.id)

        match = Match.objects.create(player1=request.user, status=Match.Status.WAITING)
        return redirect("pvp_match", match_id=match.id)


@login_required
def pvp_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.user.id not in [match.player1_id, match.player2_id]:
        return redirect("pvp_hub")
    return render(request, "pvp_match.html", {"match": match})


@login_required
def pvp_match_status(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.user.id not in [match.player1_id, match.player2_id]:
        return HttpResponseForbidden("no access")
    return JsonResponse(_state_dict(match))


@require_POST
@login_required
def pvp_cancel_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.user.id not in [match.player1_id, match.player2_id]:
        return HttpResponseForbidden("no access")

    with transaction.atomic():
        match = Match.objects.select_for_update().get(id=match_id)

        if match.status in [Match.Status.FINISHED, Match.Status.CANCELLED, Match.Status.TECHNICAL]:
            return redirect("pvp_hub")

        started = bool(
            match.status == Match.Status.ACTIVE and
            match.player2_id and
            match.started_at and
            match.expires_at
        )

        if not started:
            match.status = Match.Status.CANCELLED
            match.result = Match.Result.CANCELLED
            match.ended_at = timezone.now()
            match.winner = None
            match.save(update_fields=["status", "result", "ended_at", "winner"])
            _broadcast_state(match.id)
            return redirect("pvp_hub")

        match = Match.objects.select_related("player1", "player2").get(id=match_id)
        p1, p2 = match.player1, match.player2

        surrender_is_p1 = (request.user.id == match.player1_id)

        if surrender_is_p1:
            result = Match.Result.P2_WIN
            s1 = 0.0
        else:
            result = Match.Result.P1_WIN
            s1 = 1.0

        match.p1_rating_before = p1.rating
        match.p2_rating_before = p2.rating

        r1, r2 = update_elo(p1.rating, p2.rating, s1, k=32)
        p1.rating = r1
        p2.rating = r2
        p1.save(update_fields=["rating"])
        p2.save(update_fields=["rating"])

        match.p1_rating_after = r1
        match.p2_rating_after = r2

        match.status = Match.Status.FINISHED
        match.result = result
        match.ended_at = timezone.now()
        match.winner = p1 if result == Match.Result.P1_WIN else p2

        match.save(update_fields=[
            "p1_rating_before", "p2_rating_before",
            "p1_rating_after", "p2_rating_after",
            "status", "result", "ended_at", "winner"
        ])

        _broadcast_state(match.id)

    return redirect("pvp_hub")
