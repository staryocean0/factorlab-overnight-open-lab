from __future__ import annotations
import math
from scipy.stats import fisher_exact

Z95 = 1.959963984540054


def prob(x: int, n: int) -> float | None:
    return None if n <= 0 else x / n


def wilson_interval(x: int, n: int, z: float = Z95) -> tuple[float | None, float | None]:
    if n <= 0:
        return None, None
    p = x / n
    z2 = z * z
    den = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / den
    half = z * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / den
    return max(0.0, center - half), min(1.0, center + half)


def newcombe_hybrid_score_diff(
    x1: int, n1: int, x2: int, n2: int, z: float = Z95
) -> tuple[float | None, float | None]:
    if n1 <= 0 or n2 <= 0:
        return None, None
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson_interval(x1, n1, z)
    l2, u2 = wilson_interval(x2, n2, z)
    d = p1 - p2
    lower = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def fisher_two_sided(x1: int, n1: int, x2: int, n2: int) -> float | None:
    if n1 <= 0 or n2 <= 0 or not (0 <= x1 <= n1 and 0 <= x2 <= n2):
        return None
    return float(fisher_exact([[x1, n1 - x1], [x2, n2 - x2]], alternative="two-sided").pvalue)


def bh_adjust(pvalues: list[float | None]) -> list[float | None]:
    valid = [(i, p) for i, p in enumerate(pvalues) if p is not None and math.isfinite(p)]
    out: list[float | None] = [None] * len(pvalues)
    if not valid:
        return out
    ranked = sorted(valid, key=lambda t: (t[1], t[0]))
    m = len(ranked)
    running = 1.0
    adjusted: dict[int, float] = {}
    for rank_from_end in range(m - 1, -1, -1):
        idx, p = ranked[rank_from_end]
        rank = rank_from_end + 1
        running = min(running, p * m / rank)
        adjusted[idx] = min(1.0, running)
    for idx, value in adjusted.items():
        out[idx] = value
    return out


def rest_counts(parent_n: int, parent_x: int, bucket_n: int, bucket_x: int) -> tuple[int, int]:
    rest_n = parent_n - bucket_n
    rest_x = parent_x - bucket_x
    if rest_n < 0 or rest_x < 0 or rest_x > rest_n:
        raise ValueError("bucket is not a valid subset of parent")
    return rest_n, rest_x


def effect_metrics(bucket_x: int, bucket_n: int, parent_x: int, parent_n: int) -> dict:
    pb = prob(bucket_x, bucket_n)
    pp = prob(parent_x, parent_n)
    lift_pp = None if pb is None or pp is None else 100.0 * (pb - pp)
    rr = None if pb is None or pp is None or pp <= 0 else pb / pp
    return {"p_bucket": pb, "p_parent": pp, "lift_pp": lift_pp, "risk_ratio": rr}


def base_gate_vector(
    *, pooled_bucket_n: int, annual_bucket_n: dict[str, int], metrics: dict,
    ci_lower: float | None, annual_diffs: dict[str, float | None],
    min_pooled: int = 30, min_year: int = 5, min_lift_pp: float = 12.5,
    min_rr: float = 1.5,
) -> dict:
    lift = metrics["lift_pp"]
    rr = metrics["risk_ratio"]
    return {
        "pooled_n": pooled_bucket_n >= min_pooled,
        "annual_n": all(annual_bucket_n.get(y, 0) >= min_year for y in ("2018", "2019", "2020")),
        "positive_parent_enrichment": metrics["p_bucket"] is not None and metrics["p_parent"] is not None and metrics["p_bucket"] > metrics["p_parent"],
        "material_effect": (lift is not None and lift >= min_lift_pp) or (rr is not None and rr >= min_rr),
        "newcombe_lower_gt_zero": ci_lower is not None and ci_lower > 0,
        "annual_bucket_minus_rest_positive": all(annual_diffs.get(y) is not None and annual_diffs[y] > 0 for y in ("2018", "2019", "2020")),
    }


def final_pass(gates: dict, qvalue: float | None, return_direction_gate: bool | None = None) -> bool:
    ok = all(bool(v) for v in gates.values()) and qvalue is not None and qvalue <= 0.10
    if return_direction_gate is not None:
        ok = ok and return_direction_gate
    return bool(ok)
