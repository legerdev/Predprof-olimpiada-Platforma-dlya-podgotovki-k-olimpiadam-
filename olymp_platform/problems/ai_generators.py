import random
import math
from dataclasses import dataclass

def _choose_int(a, b):
    return random.randint(a, b)

def _gcd(a, b):
    return math.gcd(a, b)

def _lcm(a, b):
    return abs(a*b) // math.gcd(a, b)

def _nCk(n, k):
    return math.comb(n, k)

def _reduce_fraction(p, q):
    g = math.gcd(p, q)
    p //= g
    q //= g
    return f"{p}/{q}"

def gen_linear_eq_int_v1():
    while True:
        a = _choose_int(2, 12)
        b = _choose_int(-20, 20)
        c = _choose_int(-20, 40)
        if (c - b) % a == 0:
            x = (c - b) // a
            return {"a": a, "b": b, "c": c}, str(x)

def gen_ap_nth_term_v1():
    a1 = _choose_int(-20, 20)
    d = _choose_int(1, 10)
    n = _choose_int(10, 30)
    an = a1 + (n - 1) * d
    return {"a1": a1, "d": d, "n": n, "an": an}, str(an)

def gen_ap_sum_v1():
    a1 = _choose_int(-10, 10)
    d = _choose_int(1, 8)
    n = _choose_int(8, 20)
    sn = n * (2*a1 + (n-1)*d) // 2
    return {"a1": a1, "d": d, "n": n, "sn": sn}, str(sn)

def gen_gcd_v1():
    a = _choose_int(60, 500)
    b = _choose_int(60, 500)
    return {"a": a, "b": b}, str(_gcd(a, b))

def gen_lcm_v1():
    a = _choose_int(10, 120)
    b = _choose_int(10, 120)
    return {"a": a, "b": b}, str(_lcm(a, b))

def gen_divisors_count_v1():
    primes = [2, 3, 5, 7]
    while True:
        exps = [random.randint(1, 4), random.randint(0, 3), random.randint(0, 2), random.randint(0, 2)]
        n = 1
        for p, e in zip(primes, exps):
            n *= p ** e
        if 60 <= n <= 2000:
            tau = 1
            for e in exps:
                tau *= (e + 1)
            return {"n": n, "exps": exps, "tau": tau}, str(tau)

def gen_grid_paths_v1():
    m = _choose_int(2, 8)
    n = _choose_int(2, 8)
    ways = _nCk(m + n, m)
    return {"m": m, "n": n, "ways": ways}, str(ways)

def gen_right_triangle_area_v1():
    while True:
        a = _choose_int(3, 20)
        b = _choose_int(3, 20)
        if (a * b) % 2 == 0:
            area = (a * b) // 2
            return {"a": a, "b": b, "area": area}, str(area)

def gen_polygon_diagonals_v1():
    n = _choose_int(6, 20)
    d = n * (n - 3) // 2
    return {"n": n, "d": d}, str(d)

def gen_prob_two_red_v1():
    r = _choose_int(4, 10)
    b = _choose_int(2, 10)
    p = _nCk(r, 2)
    q = _nCk(r + b, 2)
    return {"r": r, "b": b, "p": p, "q": q}, _reduce_fraction(p, q)

REGISTRY = {
    "linear_eq_int_v1": gen_linear_eq_int_v1,
    "ap_nth_term_v1": gen_ap_nth_term_v1,
    "ap_sum_v1": gen_ap_sum_v1,
    "gcd_v1": gen_gcd_v1,
    "lcm_v1": gen_lcm_v1,
    "divisors_count_v1": gen_divisors_count_v1,
    "grid_paths_v1": gen_grid_paths_v1,
    "right_triangle_area_v1": gen_right_triangle_area_v1,
    "polygon_diagonals_v1": gen_polygon_diagonals_v1,
    "prob_two_red_v1": gen_prob_two_red_v1,
}
