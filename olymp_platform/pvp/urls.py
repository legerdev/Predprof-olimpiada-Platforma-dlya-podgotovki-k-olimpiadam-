from django.urls import path
from .views import pvp_hub, pvp_start_queue, pvp_match, pvp_match_status, pvp_cancel_match

urlpatterns = [
    path("pvp/", pvp_hub, name="pvp_hub"),
    path("pvp/start/", pvp_start_queue, name="pvp_start_queue"),
    path("pvp/match/<int:match_id>/", pvp_match, name="pvp_match"),
    path("pvp/match/<int:match_id>/status/", pvp_match_status, name="pvp_match_status"),
    path("pvp/match/<int:match_id>/cancel/", pvp_cancel_match, name="pvp_cancel_match"),
]
