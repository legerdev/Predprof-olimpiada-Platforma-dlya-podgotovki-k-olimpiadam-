from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone

from .models import Problem
from .utils import normalize_answer
from training.models import Submission

from django.shortcuts import redirect
from .ai_service import generate_problem_random_template


def problems_list(request):
    qs = Problem.objects.all().order_by("-created_at")

    subject = request.GET.get("subject", "").strip()
    topic = request.GET.get("topic", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()

    if subject:
        qs = qs.filter(subject=subject)

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if difficulty.isdigit():
        qs = qs.filter(difficulty=int(difficulty))

    context = {
        "problems": qs,
        "subjects": Problem.SUBJECT_CHOICES,
        "selected_subject": subject,
        "selected_topic": topic,
        "selected_difficulty": difficulty,
    }
    return render(request, "problems_list.html", context)


@login_required
def problem_detail(request, pk: int):
    """
    Показываем задачу + ставим старт таймера в session
    """
    problem = get_object_or_404(Problem, pk=pk)

    request.session["training_start_ts"] = timezone.now().timestamp()

    return render(request, "problem_detail.html", {"problem": problem, "answered": False})



@login_required
def solve_problem(request, pk: int):
    """
    Принимаем POST с ответом и time_spent,
    проверяем, сохраняем Submission,
    возвращаем на ту же страницу с результатом.
    """
    problem = get_object_or_404(Problem, pk=pk)

    if request.method != "POST":
        return HttpResponseRedirect(reverse("problem_detail", args=[pk]))

    answer = request.POST.get("answer", "").strip()
    time_spent_raw = request.POST.get("time_spent", "0")

    try:
        time_spent = int(time_spent_raw)
    except ValueError:
        time_spent = 0

    start_ts = request.session.get("training_start_ts")
    if start_ts:
        server_spent = int(timezone.now().timestamp() - float(start_ts))
        if time_spent <= 0 or abs(server_spent - time_spent) > 120:
            time_spent = max(server_spent, 0)

    is_correct = normalize_answer(answer) == normalize_answer(problem.correct_answer)

    Submission.objects.create(
        user=request.user,
        problem=problem,
        answer=answer,
        is_correct=is_correct,
        time_spent=time_spent,
    )

    context = {
        "problem": problem,
        "answered": True,
        "result": {
            "is_correct": is_correct,
            "time_spent": time_spent,
            "your_answer": answer,
            "correct_answer": problem.correct_answer,
        }
    }
    return render(request, "problem_detail.html", context)



@login_required
def generate_ai_problem(request):
    p = generate_problem_random_template()

    return redirect("problem_detail", pk=p.id)
