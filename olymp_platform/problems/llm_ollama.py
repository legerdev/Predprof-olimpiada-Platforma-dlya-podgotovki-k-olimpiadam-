import os
import json
import re
import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")


def ollama_generate_json(prompt: str, temperature: float = 0.2) -> dict:
    """
    Просим Ollama вернуть JSON. На практике модель иногда добавляет текст,
    поэтому вырезаем первый JSON-блок.
    """
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=60,
    )
    r.raise_for_status()
    text = r.json().get("response", "").strip()

    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError(f"LLM не вернул JSON. Ответ:\n{text}")

    return json.loads(m.group(0))
