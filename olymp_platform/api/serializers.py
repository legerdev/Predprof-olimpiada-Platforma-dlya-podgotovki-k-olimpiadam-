from rest_framework import serializers
from problems.models import Problem
from training.models import Submission


class ProblemListSerializer(serializers.ModelSerializer):
    subject_label = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id", "title", "subject", "subject_label",
            "topic", "difficulty",
            "is_active", "is_generated",
        ]

    def get_subject_label(self, obj):
        return obj.get_subject_display() if hasattr(obj, "get_subject_display") else obj.subject


class ProblemDetailSerializer(serializers.ModelSerializer):
    subject_label = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id", "title", "subject", "subject_label",
            "topic", "difficulty",
            "text", "hint",
            "is_active", "is_generated",
        ]

    def get_subject_label(self, obj):
        return obj.get_subject_display() if hasattr(obj, "get_subject_display") else obj.subject


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["id", "problem", "answer", "is_correct", "time_spent", "created_at"]


class SubmitAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=255)
    time_spent = serializers.FloatField(required=False, default=0)
