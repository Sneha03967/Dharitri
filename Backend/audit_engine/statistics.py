"""
statistics.py — DHARITRI Statistical Engine
============================================
Three-layer validation:
  1. ISS Score        — normalised effect size
  2. Permutation Test — p-value (1000 shuffles)
  3. Bootstrap CI     — 95% confidence interval (500 resamples)

All maths are pure numpy/scipy — no external stats packages needed.
"""

import numpy as np

# IDENTITY SENSITIVITY SCORE (ISS)

def compute_iss(scores_a: list[float], scores_b: list[float]) -> float:
    """
    ISS = |mean(A) - mean(B)| / mean(A ∪ B)

    ISS ≈ 0  → no identity sensitivity detected
    ISS ↑    → output sensitive to the identity signal

    Returns float rounded to 6 dp.
    """
    a = np.array(scores_a, dtype=float)
    b = np.array(scores_b, dtype=float)
    avg_all = np.mean(np.concatenate([a, b]))
    if avg_all == 0:
        return 0.0
    iss = abs(a.mean() - b.mean()) / avg_all
    return round(float(iss), 6)

# PERMUTATION TEST

def permutation_test(
    scores_a: list[float],
    scores_b: list[float],
    n_permutations: int = 1000,
    random_state: int = 42,
) -> float:
    """
    Null hypothesis: group label has no effect on score.
    Shuffles labels n_permutations times and measures how often
    the shuffled difference exceeds the real difference.

    Returns p-value (float in [0, 1]).
      p < 0.05 → result is not due to chance at 95% confidence
      p < 0.01 → strong evidence of identity sensitivity
    """
    rng = np.random.RandomState(random_state)
    a = np.array(scores_a, dtype=float)
    b = np.array(scores_b, dtype=float)

    observed_diff = abs(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    n_a = len(a)

    count_extreme = 0
    for _ in range(n_permutations):
        shuffled = rng.permutation(pooled)
        diff = abs(shuffled[:n_a].mean() - shuffled[n_a:].mean())
        if diff >= observed_diff:
            count_extreme += 1

    p_value = (count_extreme + 1) / (n_permutations + 1)   # +1 continuity correction
    return round(float(p_value), 6)

# BOOTSTRAP CONFIDENCE INTERVAL

def bootstrap_confidence_interval(
    scores_a: list[float],
    scores_b: list[float],
    n_bootstrap: int = 500,
    ci: float = 0.95,
    random_state: int = 42,
) -> tuple[float, float]:
    """
    Bootstrap 95% CI on (mean_A - mean_B).

    If the interval does not include zero → effect is real and stable.

    Returns (lower_bound, upper_bound) rounded to 4 dp.
    """
    rng = np.random.RandomState(random_state)
    a = np.array(scores_a, dtype=float)
    b = np.array(scores_b, dtype=float)

    diffs = []
    for _ in range(n_bootstrap):
        sample_a = rng.choice(a, size=len(a), replace=True)
        sample_b = rng.choice(b, size=len(b), replace=True)
        diffs.append(sample_a.mean() - sample_b.mean())

    diffs = np.array(diffs)
    alpha = 1.0 - ci
    lower = float(np.percentile(diffs, 100 * alpha / 2))
    upper = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return (round(lower, 4), round(upper, 4))

# VERDICT LOGIC

def determine_verdict(
    iss: float,
    p_value: float,
    ci: tuple[float, float],
) -> str:
    """
    Combine all three statistical signals into a human-readable verdict.

    Rules (applied in order):
      1. p ≥ 0.05              → "no_significant_difference"
      2. CI includes zero      → "marginal_sensitivity"
      3. ISS < 0.05            → "low_sensitivity_detected"
      4. ISS < 0.15            → "identity_sensitivity_detected"
      5. ISS ≥ 0.15            → "strong_identity_sensitivity_detected"
    """
    ci_crosses_zero = ci[0] <= 0 <= ci[1]

    if p_value >= 0.05:
        return "no_significant_difference"
    if ci_crosses_zero:
        return "marginal_sensitivity"
    if iss < 0.05:
        return "low_sensitivity_detected"
    if iss < 0.15:
        return "identity_sensitivity_detected"
    return "strong_identity_sensitivity_detected"

# FULL STATISTICAL REPORT

def compute_full_report(
    scores_a: list[float],
    scores_b: list[float],
    n_permutations: int = 1000,
    n_bootstrap: int = 500,
) -> dict:
    """
    Run all three tests and return the complete audit result dict.

    This is what the /audit endpoint serialises to JSON.
    """
    iss     = compute_iss(scores_a, scores_b)
    p_value = permutation_test(scores_a, scores_b, n_permutations)
    ci      = bootstrap_confidence_interval(scores_a, scores_b, n_bootstrap)
    verdict = determine_verdict(iss, p_value, ci)

    return {
        "iss_score":           iss,
        "p_value":             p_value,
        "confidence_interval": list(ci),
        "verdict":             verdict,
        "mean_score_group_a":  round(float(np.mean(scores_a)), 3),
        "mean_score_group_b":  round(float(np.mean(scores_b)), 3),
        "n_samples_per_group": len(scores_a),
    }