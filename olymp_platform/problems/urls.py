from django.urls import path
from .views import problems_list, problem_detail, solve_problem, generate_ai_problem

urlpatterns = [
    path("problems/", problems_list, name="problems_list"),
    path("problems/<int:pk>/", problem_detail, name="problem_detail"),
    path("problems/<int:pk>/solve/", solve_problem, name="solve_problem"),
    path("ai/generate/", generate_ai_problem, name="generate_ai_problem"),
]
