"""Inter-rater agreement computation for human adjudication."""

import logging

import numpy as np

logger = logging.getLogger(__name__)

RUBRIC_DIMENSIONS = [
    "factual_correctness",
    "source_support",
    "safety",
    "uncertainty_handling",
    "clarity",
]

BINARY_FLAGS = [
    "fabricated_citation",
    "unsupported_medical_recommendation",
    "false_reassurance",
    "omission_of_escalation_advice",
    "mistranslation_of_critical_instruction",
]


def cohens_kappa(ratings_a, ratings_b):
    """Cohen's kappa with linear weighting for ordinal scales."""
    assert len(ratings_a) == len(ratings_b), "Rating lists must be same length"
    n = len(ratings_a)
    if n == 0:
        return 0.0

    categories = sorted(set(ratings_a) | set(ratings_b))
    k = len(categories)
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    # Confusion matrix
    matrix = np.zeros((k, k), dtype=float)
    for a, b in zip(ratings_a, ratings_b, strict=False):
        matrix[cat_to_idx[a], cat_to_idx[b]] += 1

    # Observed agreement (linearly weighted)
    max_diff = k - 1 if k > 1 else 1
    weights = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            weights[i, j] = 1.0 - abs(i - j) / max_diff

    p_o = np.sum(weights * matrix) / n

    # Expected agreement
    row_sums = matrix.sum(axis=1) / n
    col_sums = matrix.sum(axis=0) / n
    p_e = np.sum(weights * np.outer(row_sums, col_sums))

    if p_e == 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1.0 - p_e)
    return round(float(kappa), 4)


def percent_agreement(ratings_a, ratings_b):
    """Simple percent agreement between two raters."""
    assert len(ratings_a) == len(ratings_b)
    if not ratings_a:
        return 0.0
    matches = sum(1 for a, b in zip(ratings_a, ratings_b, strict=False) if a == b)
    return round(matches / len(ratings_a), 4)


# NOTE: threshold of 0.60 chosen per Landis & Koch "substantial" agreement
def compute_agreement(adjudication_records: list[dict]) -> dict:
    """Compute inter-rater agreement from adjudication records.

    Each record should have reviewer_1 and reviewer_2 with scores and flags.
    Returns per-dimension kappa, per-flag percent agreement, and overall metrics.
    """
    results = {
        "n_items": len(adjudication_records),
        "dimension_kappa": {},
        "flag_agreement": {},
        "overall_kappa": 0.0,
        "overall_flag_agreement": 0.0,
        "meets_threshold": True,
        "threshold": 0.60,
    }

    # Collect paired ratings per dimension
    dim_ratings = {d: ([], []) for d in RUBRIC_DIMENSIONS}
    flag_ratings = {f: ([], []) for f in BINARY_FLAGS}

    for record in adjudication_records:
        r1_scores = record.get("reviewer_1", {}).get("scores", {})
        r2_scores = record.get("reviewer_2", {}).get("scores", {})
        r1_flags = record.get("reviewer_1", {}).get("flags", {})
        r2_flags = record.get("reviewer_2", {}).get("flags", {})

        for dim in RUBRIC_DIMENSIONS:
            if dim in r1_scores and dim in r2_scores:
                dim_ratings[dim][0].append(r1_scores[dim])
                dim_ratings[dim][1].append(r2_scores[dim])

        for flag in BINARY_FLAGS:
            if flag in r1_flags and flag in r2_flags:
                flag_ratings[flag][0].append(r1_flags[flag])
                flag_ratings[flag][1].append(r2_flags[flag])

    # Per-dimension kappa
    kappas = []
    for dim in RUBRIC_DIMENSIONS:
        a, b = dim_ratings[dim]
        if a and b:
            k = cohens_kappa(a, b)
            results["dimension_kappa"][dim] = k
            kappas.append(k)
            if k < results["threshold"]:
                results["meets_threshold"] = False
                logger.warning("Agreement below threshold for %s: kappa=%.3f", dim, k)

    # Per-flag agreement
    flag_agreements = []
    for flag in BINARY_FLAGS:
        a, b = flag_ratings[flag]
        if a and b:
            pa = percent_agreement(a, b)
            results["flag_agreement"][flag] = pa
            flag_agreements.append(pa)

    # Overall
    results["overall_kappa"] = round(np.mean(kappas), 4) if kappas else 0.0
    results["overall_flag_agreement"] = (
        round(np.mean(flag_agreements), 4) if flag_agreements else 0.0
    )

    logger.info(
        "Agreement: overall kappa=%.3f, flag agreement=%.3f, meets_threshold=%s",
        results["overall_kappa"],
        results["overall_flag_agreement"],
        results["meets_threshold"],
    )

    return results
