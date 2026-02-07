def update_elo(r1: int, r2: int, s1: float, k: int = 32):
    """
    s1: фактический результат игрока1: 1 / 0.5 / 0
    """
    e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
    e2 = 1 - e1

    s2 = 1 - s1

    new_r1 = round(r1 + k * (s1 - e1))
    new_r2 = round(r2 + k * (s2 - e2))
    return new_r1, new_r2
