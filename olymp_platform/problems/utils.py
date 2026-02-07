def normalize_answer(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.split())
    return s
