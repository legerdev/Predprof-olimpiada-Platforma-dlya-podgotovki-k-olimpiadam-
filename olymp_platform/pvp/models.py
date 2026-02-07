from django.conf import settings
from django.db import models
from django.utils import timezone

from problems.models import Problem


class Match(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Ожидание"
        ACTIVE = "active", "Идёт"
        FINISHED = "finished", "Завершён"
        CANCELLED = "cancelled", "Отменён"
        TECHNICAL = "technical", "Техническая ошибка"

    class Result(models.TextChoices):
        P1_WIN = "p1_win", "Победа игрока 1"
        P2_WIN = "p2_win", "Победа игрока 2"
        DRAW = "draw", "Ничья"
        CANCELLED = "cancelled", "Отменён"
        TECHNICAL = "technical", "Техническая ошибка"

    class AnswerState(models.TextChoices):
        IDLE = "idle", "Не отвечал"
        WRONG = "wrong", "Неверно"
        CORRECT = "correct", "Верно"

    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pvp_matches_as_p1",
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pvp_matches_as_p2",
        null=True,
        blank=True,
    )

    problem = models.ForeignKey(
        Problem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pvp_matches",
    )

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pvp_wins",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    allow_resubmit = models.BooleanField(default=True)
    duration_sec = models.PositiveIntegerField(default=90)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    result = models.CharField(max_length=20, choices=Result.choices, null=True, blank=True)

    p1_state = models.CharField(max_length=10, choices=AnswerState.choices, default=AnswerState.IDLE)
    p2_state = models.CharField(max_length=10, choices=AnswerState.choices, default=AnswerState.IDLE)
    p1_score = models.PositiveSmallIntegerField(default=0)
    p2_score = models.PositiveSmallIntegerField(default=0)

    p1_last_answer = models.TextField(blank=True, default="")
    p2_last_answer = models.TextField(blank=True, default="")
    p1_last_submit_at = models.DateTimeField(null=True, blank=True)
    p2_last_submit_at = models.DateTimeField(null=True, blank=True)

    p1_rating_before = models.IntegerField(null=True, blank=True)
    p2_rating_before = models.IntegerField(null=True, blank=True)
    p1_rating_after = models.IntegerField(null=True, blank=True)
    p2_rating_after = models.IntegerField(null=True, blank=True)

    p1_connected = models.BooleanField(default=False)
    p2_connected = models.BooleanField(default=False)
    p1_disconnected_at = models.DateTimeField(null=True, blank=True)
    p2_disconnected_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"Match #{self.id} ({self.status})"
