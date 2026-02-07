from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from problems.models import Problem
from problems.utils import normalize_answer
from training.models import Submission

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets


from .serializers import (
    ProblemListSerializer, ProblemDetailSerializer,
    SubmitAnswerSerializer, SubmissionSerializer
)


class ProblemViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Problem.objects.filter(is_active=True).order_by("-id")

        subject = self.request.query_params.get("subject")
        topic = self.request.query_params.get("topic")
        difficulty = self.request.query_params.get("difficulty")
        dmin = self.request.query_params.get("difficulty_min")
        dmax = self.request.query_params.get("difficulty_max")

        if subject:
            qs = qs.filter(subject=subject)

        if topic:
            qs = qs.filter(topic__icontains=topic)

        if difficulty:
            try:
                qs = qs.filter(difficulty=int(difficulty))
            except ValueError:
                pass

        if dmin:
            try:
                qs = qs.filter(difficulty__gte=int(dmin))
            except ValueError:
                pass

        if dmax:
            try:
                qs = qs.filter(difficulty__lte=int(dmax))
            except ValueError:
                pass

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProblemDetailSerializer
        return ProblemListSerializer

    @action(methods=["POST"], detail=True, url_path="submit")
    def submit(self, request, pk=None):
        problem = self.get_object()
        ser = SubmitAnswerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        answer = ser.validated_data["answer"]
        time_spent = ser.validated_data.get("time_spent", 0) or 0

        is_correct = normalize_answer(answer) == normalize_answer(problem.correct_answer)

        sub = Submission.objects.create(
            user=request.user,
            problem=problem,
            answer=answer,
            is_correct=is_correct,
            time_spent=time_spent,
        )

        return Response({
            "correct": is_correct,
            "submission": SubmissionSerializer(sub).data,
            "hint": problem.hint if (not is_correct and problem.hint) else None,
        }, status=status.HTTP_200_OK)
