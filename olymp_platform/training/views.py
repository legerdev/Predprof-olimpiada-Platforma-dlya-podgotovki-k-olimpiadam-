from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import render

from .models import Submission


@login_required
def analytics_view(request):
    submissions = Submission.objects.filter(user=request.user).select_related("problem")

    total = submissions.count()
    correct = submissions.filter(is_correct=True).count()

    accuracy = round((correct / total) * 100, 1) if total > 0 else 0
    avg_time = submissions.aggregate(avg=Avg("time_spent"))["avg"] or 0
    avg_time = round(avg_time, 1)

    raw = (
        submissions
        .values("problem__topic")
        .annotate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
        )
        .order_by("-total")
    )

    topics_stats = []
    for r in raw:
        topic = r["problem__topic"] or "Без темы"
        tot = r["total"]
        cor = r["correct"]
        acc = round((cor / tot) * 100, 1) if tot else 0
        topics_stats.append({
            "topic": topic,
            "total": tot,
            "correct": cor,
            "accuracy": acc,
        })

    progress = (
        submissions
        .extra(select={"day": "date(created_at)"})
        .values("day")
        .annotate(correct=Count("id", filter=Q(is_correct=True)))
        .order_by("day")
    )

    dates = [str(p["day"]) for p in progress]
    values = [p["correct"] for p in progress]

    context = {
        "total": total,
        "accuracy": accuracy,
        "avg_time": avg_time,
        "topics_stats": topics_stats,
        "dates": dates,
        "values": values,
    }
    return render(request, "analytics.html", context)
