"""Statistical analysis -- confidence intervals, comparisons, stratified results."""

from __future__ import annotations

import logging
from collections import defaultdict

import numpy as np
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)

RUBRIC_DIMENSIONS = [
    "factual_correctness",
    "source_support",
    "safety",
    "uncertainty_handling",
    "clarity",
]

SYSTEMS = ["llm_only", "rag", "citation_rag", "agent_pipeline"]


def bootstrap_ci(
    values: list[float],
    n_bootstrap: int = 10000,
    ci: float = 0.95,
    statistic: str = "mean",
):
    """Bootstrap confidence interval.  Returns (point_estimate, ci_lower, ci_upper)."""
    arr = np.array(values)
    if len(arr) == 0:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(42)
    stat_fn = np.mean if statistic == "mean" else np.median

    point = float(stat_fn(arr))
    boot_stats = []
    for _ in range(n_bootstrap):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_stats.append(float(stat_fn(sample)))

    alpha = (1 - ci) / 2
    lower = float(np.percentile(boot_stats, alpha * 100))
    upper = float(np.percentile(boot_stats, (1 - alpha) * 100))

    return round(point, 4), round(lower, 4), round(upper, 4)


def compute_main_results(eval_results: list[dict]) -> dict:
    """Mean scores per system per metric, with bootstrap CIs.

    Returns a nested dict: {system: {metric: {mean, ci_lower, ci_upper}}}.
    """
    by_system: dict[str, list[dict]] = defaultdict(list)
    for r in eval_results:
        by_system[r["system"]].append(r)

    results: dict[str, dict] = {}

    for system, evals in by_system.items():
        results[system] = {}

        for dim in RUBRIC_DIMENSIONS:
            vals = [e["scores"].get(dim, 0) for e in evals]
            mean, lower, upper = bootstrap_ci(vals)
            results[system][dim] = {"mean": mean, "ci_lower": lower, "ci_upper": upper}

        # GSS
        gss_vals = [e["composite_scores"]["grounded_safety_score"] for e in evals]
        mean, lower, upper = bootstrap_ci(gss_vals)
        results[system]["grounded_safety_score"] = {
            "mean": mean,
            "ci_lower": lower,
            "ci_upper": upper,
        }

        # Binary flag rates
        for flag in [
            "fabricated_citation",
            "unsupported_medical_recommendation",
            "false_reassurance",
            "omission_of_escalation_advice",
        ]:
            flag_vals = [1.0 if e["binary_flags"].get(flag, False) else 0.0 for e in evals]
            rate = np.mean(flag_vals) if flag_vals else 0.0
            results[system][f"{flag}_rate"] = round(float(rate), 4)

    return results


def paired_comparison(
    eval_results: list[dict],
    system_a: str,
    system_b: str,
    metric: str = "grounded_safety_score",
) -> dict:
    """Paired Wilcoxon signed-rank comparison between two systems."""
    # Match by item_id
    a_by_item = {}
    b_by_item = {}

    for r in eval_results:
        item_id = r["item_id"]
        if r["system"] == system_a:
            if metric == "grounded_safety_score":
                a_by_item[item_id] = r["composite_scores"]["grounded_safety_score"]
            else:
                a_by_item[item_id] = r["scores"].get(metric, 0)
        elif r["system"] == system_b:
            if metric == "grounded_safety_score":
                b_by_item[item_id] = r["composite_scores"]["grounded_safety_score"]
            else:
                b_by_item[item_id] = r["scores"].get(metric, 0)

    shared_ids = sorted(set(a_by_item.keys()) & set(b_by_item.keys()))
    # print(f"[debug] paired comparison: {len(shared_ids)} shared items")
    if len(shared_ids) < 10:
        return {
            "system_a": system_a,
            "system_b": system_b,
            "metric": metric,
            "n_pairs": len(shared_ids),
            "note": "Too few pairs for reliable comparison",
        }

    vals_a = [a_by_item[i] for i in shared_ids]
    vals_b = [b_by_item[i] for i in shared_ids]
    diffs = [a - b for a, b in zip(vals_a, vals_b, strict=False)]

    try:
        stat, p_value = scipy_stats.wilcoxon(diffs)
    except ValueError:
        stat, p_value = 0.0, 1.0

    # Effect size (rank-biserial correlation)
    n = len(diffs)
    effect_size = float(stat) / (n * (n + 1) / 2) if n > 0 else 0.0

    return {
        "system_a": system_a,
        "system_b": system_b,
        "metric": metric,
        "n_pairs": len(shared_ids),
        "mean_a": round(float(np.mean(vals_a)), 4),
        "mean_b": round(float(np.mean(vals_b)), 4),
        "mean_diff": round(float(np.mean(diffs)), 4),
        "wilcoxon_stat": round(float(stat), 4),
        "p_value": round(float(p_value), 6),
        "effect_size": round(effect_size, 4),
    }


def stratified_results(
    eval_results: list[dict],
    items: list[dict],
    stratify_by: str = "topic",
) -> dict:
    """Results stratified by a benchmark item field (topic, task_family, language).

    Returns {stratum_value: {system: {metric: mean}}}.
    """
    item_by_id = {item["item_id"]: item for item in items}

    groups: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    for r in eval_results:
        item = item_by_id.get(r["item_id"], {})
        stratum = item.get(stratify_by, "unknown")
        groups[stratum][r["system"]].append(r)

    results: dict[str, dict] = {}
    for stratum, systems in groups.items():
        results[stratum] = {}
        for system, evals in systems.items():
            gss_vals = [e["composite_scores"]["grounded_safety_score"] for e in evals]
            results[stratum][system] = {
                "n": len(evals),
                "gss_mean": round(float(np.mean(gss_vals)), 4) if gss_vals else 0.0,
            }
            for dim in RUBRIC_DIMENSIONS:
                dim_vals = [e["scores"].get(dim, 0) for e in evals]
                results[stratum][system][dim] = (
                    round(float(np.mean(dim_vals)), 4) if dim_vals else 0.0
                )

    return results
