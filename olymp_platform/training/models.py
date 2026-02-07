from django.conf import settings
from django.db import models
from problems.models import Problem

class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    time_spent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} -> {self.problem} ({'OK' if self.is_correct else 'NO'})"
