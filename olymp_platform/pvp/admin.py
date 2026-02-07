from django.contrib import admin
from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "result", "player1", "player2", "created_at", "ended_at")
    list_filter = ("status", "result", "created_at")
    search_fields = ("player1__username", "player2__username")
    ordering = ("-created_at",)
    autocomplete_fields = ("player1", "player2", "winner", "problem")

    readonly_fields = (
        "created_at", "ended_at",
        "p1_rating_before", "p2_rating_before", "p1_rating_after", "p2_rating_after",
        "p1_score", "p2_score", "p1_state", "p2_state",
    )
