import math


def solve_linear_eq_int_v1(p):
    a, b, c = int(p["a"]), int(p["b"]), int(p["c"])
    return str((c - b) // a)

def solve_ap_nth_term_v1(p):
    a1, d, n = int(p["a1"]), int(p["d"]), int(p["n"])
    return str(a1 + (n - 1) * d)

def solve_ap_sum_v1(p):
    a1, d, n = int(p["a1"]), int(p["d"]), int(p["n"])
    return str(n * (2*a1 + (n-1)*d) // 2)

def solve_gcd_v1(p):
    return str(math.gcd(int(p["a"]), int(p["b"])))

def solve_lcm_v1(p):
    a, b = int(p["a"]), int(p["b"])
    return str(abs(a*b) // math.gcd(a, b))

def solve_divisors_count_v1(p):
    n = int(p["n"])
    x = n
    ans = 1
    d = 2
    while d*d <= x:
        if x % d == 0:
            e = 0
            while x % d == 0:
                x //= d
                e += 1
            ans *= (e + 1)
        d += 1
    if x > 1:
        ans *= 2
    return str(ans)

def solve_grid_paths_v1(p):
    m, n = int(p["m"]), int(p["n"])
    return str(math.comb(m+n, m))

def solve_right_triangle_area_v1(p):
    a, b = int(p["a"]), int(p["b"])
    return str((a*b)//2)

def solve_polygon_diagonals_v1(p):
    n = int(p["n"])
    return str(n*(n-3)//2)

def solve_prob_two_red_v1(p):
    r, b = int(p["r"]), int(p["b"])
    num = math.comb(r, 2)
    den = math.comb(r+b, 2)
    g = math.gcd(num, den)
    return f"{num//g}/{den//g}"


SOLVERS = {
    "linear_eq_int_v1": solve_linear_eq_int_v1,
    "ap_nth_term_v1": solve_ap_nth_term_v1,
    "ap_sum_v1": solve_ap_sum_v1,
    "gcd_v1": solve_gcd_v1,
    "lcm_v1": solve_lcm_v1,
    "divisors_count_v1": solve_divisors_count_v1,
    "grid_paths_v1": solve_grid_paths_v1,
    "right_triangle_area_v1": solve_right_triangle_area_v1,
    "polygon_diagonals_v1": solve_polygon_diagonals_v1,
    "prob_two_red_v1": solve_prob_two_red_v1,
}
