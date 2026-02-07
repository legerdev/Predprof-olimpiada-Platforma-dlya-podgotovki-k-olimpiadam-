import random
from django.db import transaction
from django.utils import timezone

from .models import Problem, ProblemTemplate
from .ai_solvers import SOLVERS
from .llm_ollama import ollama_generate_json


def _build_prompt(tpl: ProblemTemplate) -> str:
    return f"""
Ты генерируешь параметры для олимпиадной задачи.
Верни ТОЛЬКО JSON без текста вокруг.

Тема: {tpl.topic}
Сложность: {tpl.difficulty}

Шаблон текста (в нём плейсхолдеры параметров):
{tpl.statement_template}

Схема параметров и ограничения (подсказка):
{tpl.params_schema}

Формат ответа строго такой:
{{
  "params": {{
    "a": 1,
    "b": 2
  }}
}}

Требования:
- params должен содержать ВСЕ ключи, которые используются в фигурных скобках шаблона.
- Числа — целые, если не сказано иначе.
- Подбирай значения так, чтобы задача имела корректный “красивый” ответ (целый/дробь в нужном формате).
""".strip()


def _trim_pool(template):
    pool_max = getattr(template, "pool_max", 30) or 30

    qs = (
        Problem.objects
        .filter(is_generated=True, source_template=template, is_active=True)
        .order_by("generated_at", "id")
    )
    cnt = qs.count()
    if cnt <= pool_max:
        return

    excess = cnt - pool_max
    qs[:excess].update(is_active=False)


@transaction.atomic
def generate_problem_random_template() -> Problem:
    tpl = (
        ProblemTemplate.objects
        .select_for_update()
        .filter(is_active=True)
        .order_by("?")
        .first()
    )
    if not tpl:
        raise RuntimeError("Нет активных шаблонов ProblemTemplate")

    return generate_problem_from_template(tpl)


@transaction.atomic
def generate_problem_from_template(tpl: ProblemTemplate) -> Problem:
    key = getattr(tpl, "solver_key", None) or getattr(tpl, "generator_key", None)
    if not key:
        raise RuntimeError("У шаблона нет generator_key/solver_key")

    solver = SOLVERS.get(key)
    if not solver:
        raise RuntimeError(f"Нет solver для ключа: {key}")

    prompt = _build_prompt(tpl)
    data = ollama_generate_json(prompt)

    params = data.get("params")
    if not isinstance(params, dict):
        raise ValueError(f"Неверный JSON от LLM: {data}")

    text = tpl.statement_template.format(**params)
    correct = solver(params)

    hint_text = ""
    if getattr(tpl, "hint", ""):
        try:
            hint_text = tpl.hint.format(**params)
        except Exception:
            hint_text = tpl.hint

    if Problem.objects.filter(source_template=tpl, gen_params=params, is_active=True).exists():
        data2 = ollama_generate_json(prompt)
        params2 = data2.get("params")
        if not isinstance(params2, dict):
            raise ValueError(f"Неверный JSON от LLM: {data2}")
        text = tpl.statement_template.format(**params2)
        correct = solver(params2)
        params = params2

    p = Problem.objects.create(
        title=tpl.display_title,
        text=text,
        subject=tpl.subject,
        topic=tpl.topic,
        difficulty=tpl.difficulty,
        correct_answer=str(correct),
        hint=hint_text,
        is_generated=True,
        is_active=True,
        source_template=tpl,
        gen_params=params,
        generated_at=timezone.now(),
    )

    _trim_pool(tpl)
    return p

