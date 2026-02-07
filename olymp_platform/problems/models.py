from django.db import models

class Problem(models.Model):
    SUBJECT_CHOICES = [
        ("math", "Математика"),
        ("informatics", "Информатика"),
        ("physics", "Физика"),
        ("chemistry", "Химия"),
        ("biology", "Биология"),
        ("russian", "Русский"),
        ("english", "Английский"),
        ("social", "Обществознание"),
        ("history", "История"),
        ("geo", "География"),
    ]

    title = models.CharField(max_length=255, verbose_name="Название")
    subject = models.CharField(max_length=32, choices=SUBJECT_CHOICES, verbose_name="Предмет")
    topic = models.CharField(max_length=120, verbose_name="Тема")
    difficulty = models.PositiveSmallIntegerField(default=1, verbose_name="Сложность (1-10)")
    text = models.TextField(verbose_name="Текст задачи")

    correct_answer = models.CharField(max_length=255, verbose_name="Правильный ответ")

    hint = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    is_generated = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    source_template = models.ForeignKey(
        "problems.ProblemTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_problems"
    )
    gen_params = models.JSONField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    

    def __str__(self):
        return f"[{self.get_subject_display()}] {self.title} (сложн. {self.difficulty})"


class ProblemTemplate(models.Model):
    key = models.CharField(max_length=64, unique=True)
    display_title = models.CharField(max_length=200)
    subject = models.CharField(max_length=32)
    topic = models.CharField(max_length=128)
    difficulty = models.PositiveSmallIntegerField(default=2)

    statement_template = models.TextField()
    generator_key = models.CharField(max_length=64)
    params_schema = models.JSONField(default=dict, blank=True)

    hint = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.key} [{self.subject}/{self.topic}]"