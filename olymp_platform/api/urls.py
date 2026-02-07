from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProblemViewSet
from .auth_views import TokenAuthView

router = DefaultRouter()
router.register(r"problems", ProblemViewSet, basename="problems")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", TokenAuthView.as_view(), name="api_token"),
]
