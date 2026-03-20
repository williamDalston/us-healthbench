"""
Generate a stratified human-adjudication sample of 50 items from the
US-HealthBench experiment.

Strata
------
- 15 factual_retrieval   (task_family == "factual_retrieval", not abstention)
- 12 consumer_action     (task_family == "consumer_action",  not abstention)
- 10 misinformation_rebuttal (task_family == "misinformation_rebuttal", not abstention)
-  8 cross_language       (task_family == "cross_language",   not abstention)
-  5 abstention           (flags.requires_abstention == true, any task_family)

Within each stratum the items are spread across GSS (grounded_safety_score)
quintiles so that the sample contains a mix of high- and low-scoring items.

Outputs
-------
- data/experiment/human_adjudication_sample.jsonl
- data/experiment/adjudication_sample_stats.json
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

# --- paths (relative to repo root) ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_PATH = REPO_ROOT / "data" / "benchmark_v1" / "benchmark_items.jsonl"
OUTPUTS_PATH = REPO_ROOT / "data" / "experiment" / "outputs_agent_pipeline.jsonl"
EVALS_PATH = REPO_ROOT / "data" / "experiment" / "eval_agent_pipeline.jsonl"
SAMPLE_PATH = REPO_ROOT / "data" / "experiment" / "human_adjudication_sample.jsonl"
STATS_PATH = REPO_ROOT / "data" / "experiment" / "adjudication_sample_stats.json"

SEED = 42

# desired sample sizes per stratum
STRATA_SIZES = {
    "factual_retrieval": 15,
    "consumer_action": 12,
    "misinformation_rebuttal": 10,
    "cross_language": 8,
    "abstention": 5,
}
TOTAL_SAMPLE = sum(STRATA_SIZES.values())  # 50


# helpers


def load_jsonl(path: Path) -> list[dict]:
    recs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def assign_stratum(item: dict) -> str:
    """Determine sampling stratum for a benchmark item.

    Abstention items go into "abstention" regardless of task_family.
    Everything else maps to its task_family directly.
    """
    if item["flags"].get("requires_abstention", False):
        return "abstention"
    return item["task_family"]


# FIXME: pick_spread could be made more robust for very small pools
def pick_spread(candidates, n, rng):
    """From candidates (sorted by GSS asc), pick n spread across the range."""
    if len(candidates) <= n:
        return list(candidates)

    bin_sz = len(candidates) / n
    selected = []
    used = set()

    for i in range(n):
        lo = int(math.floor(i * bin_sz))
        hi = int(math.floor((i + 1) * bin_sz))
        hi = min(hi, len(candidates))
        pool = [idx for idx in range(lo, hi) if idx not in used]
        if not pool:
            pool = [idx for idx in range(len(candidates)) if idx not in used]
        chosen = rng.choice(pool)
        used.add(chosen)
        selected.append(candidates[chosen])

    return selected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    rng = random.Random(SEED)

    # 1. Load data
    print(f"Loading benchmark items from {BENCHMARK_PATH} ...")
    items = load_jsonl(BENCHMARK_PATH)
    items_by_id = {it["item_id"]: it for it in items}
    print(f"  -> {len(items)} items loaded.")

    print(f"Loading agent_pipeline outputs from {OUTPUTS_PATH} ...")
    outputs = load_jsonl(OUTPUTS_PATH)
    outputs_by_id = {o["item_id"]: o for o in outputs}
    print(f"  -> {len(outputs)} outputs loaded.")

    print(f"Loading eval results from {EVALS_PATH} ...")
    evals = load_jsonl(EVALS_PATH)
    evals_by_id = {e["item_id"]: e for e in evals}
    print(f"  -> {len(evals)} eval records loaded.")

    # 2. Merged lookup -- only keep items present in all three datasets
    common_ids = set(items_by_id) & set(outputs_by_id) & set(evals_by_id)
    print(f"  -> {len(common_ids)} items present in all three files.")

    # 3. Bucket by stratum
    strata: dict[str, list[dict]] = defaultdict(list)
    for iid in common_ids:
        item = items_by_id[iid]
        stratum = assign_stratum(item)
        gss = evals_by_id[iid]["composite_scores"].get("grounded_safety_score")
        if gss is None:
            gss = 0.0  # treat missing GSS as 0 for sorting
        strata[stratum].append(
            {
                "_item_id": iid,
                "_gss": gss,
            }
        )

    print("\nStratum pool sizes:")
    for sname in STRATA_SIZES:
        print(f"  {sname}: {len(strata[sname])} available, need {STRATA_SIZES[sname]}")

    # 4. Stratified sampling with GSS spread
    sampled_ids = []

    for stratum_name, target_n in STRATA_SIZES.items():
        pool = strata[stratum_name]
        if len(pool) < target_n:
            print(
                f"  WARNING: stratum '{stratum_name}' has only {len(pool)} items "
                f"(need {target_n}). Taking all available."
            )
        pool.sort(key=lambda x: x["_gss"])
        picks = pick_spread(pool, target_n, rng)
        sampled_ids.extend(p["_item_id"] for p in picks)

    assert len(sampled_ids) == TOTAL_SAMPLE, (
        f"Expected {TOTAL_SAMPLE} samples, got {len(sampled_ids)}"
    )
    print(f"\nTotal sampled: {len(sampled_ids)}")

    # 5. Build output records
    sample_records = []
    for iid in sampled_ids:
        item = items_by_id[iid]
        output = outputs_by_id[iid]
        ev = evals_by_id[iid]

        record = {
            # identification & metadata
            "item_id": iid,
            "question": item["question"],
            "task_family": item["task_family"],
            "topic": item["topic"],
            "language": item["language"],
            "difficulty": item["difficulty"],
            # reference answer
            "reference_answer_text": item["reference_answer"]["answer_text"],
            "required_points": item["reference_answer"]["required_points"],
            # system answer
            "system_answer_text": output["answer_text"],
            # automated evaluation
            "automated_scores": ev["scores"],
            "binary_flags": ev["binary_flags"],
            "composite_scores": ev["composite_scores"],
            # human adjudication (to be filled in)
            "human_scores": {
                "factual_correctness": None,
                "source_support": None,
                "safety": None,
                "uncertainty_handling": None,
                "clarity": None,
            },
        }
        sample_records.append(record)

    # 6. Write sample JSONL
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_PATH, "w", encoding="utf-8") as fh:
        for rec in sample_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nSample written to {SAMPLE_PATH}")

    # 7. Summary statistics
    stratum_counter: Counter = Counter()
    difficulty_counter: Counter = Counter()
    lang_counter: Counter = Counter()
    topic_counter: Counter = Counter()
    gss_vals_by_stratum: dict[str, list[float]] = defaultdict(list)

    for rec in sample_records:
        s = assign_stratum(items_by_id[rec["item_id"]])
        stratum_counter[s] += 1
        difficulty_counter[rec["difficulty"]] += 1
        lang_counter[rec["language"]] += 1
        topic_counter[rec["topic"]] += 1
        gss = rec["composite_scores"].get("grounded_safety_score")
        if gss is not None:
            gss_vals_by_stratum[s].append(gss)

    gss_summary: dict[str, dict] = {}
    for s, vals in gss_vals_by_stratum.items():
        vals_sorted = sorted(vals)
        gss_summary[s] = {
            "count": len(vals_sorted),
            "min": round(vals_sorted[0], 4) if vals_sorted else None,
            "max": round(vals_sorted[-1], 4) if vals_sorted else None,
            "mean": round(sum(vals_sorted) / len(vals_sorted), 4) if vals_sorted else None,
            "median": round(vals_sorted[len(vals_sorted) // 2], 4) if vals_sorted else None,
        }

    stats = {
        "total_sampled": len(sample_records),
        "strata_requested": STRATA_SIZES,
        "strata_actual": dict(stratum_counter),
        "difficulty_distribution": dict(difficulty_counter),
        "language_distribution": dict(lang_counter),
        "topic_distribution": dict(topic_counter),
        "gss_summary_by_stratum": gss_summary,
        "seed": SEED,
    }

    with open(STATS_PATH, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2, ensure_ascii=False)
    print(f"Stats written to  {STATS_PATH}")

    # Quick sanity print
    print("\n=== Sample Composition ===")
    for s in STRATA_SIZES:
        n = stratum_counter.get(s, 0)
        gs = gss_summary.get(s, {})
        print(
            f"  {s:30s}  n={n:2d}  GSS range: "
            f"[{gs.get('min', '?')}, {gs.get('max', '?')}]  "
            f"mean={gs.get('mean', '?')}"
        )
    print(f"\nDifficulty: {dict(difficulty_counter)}")
    print(f"Language:   {dict(lang_counter)}")
    print("Done.")


if __name__ == "__main__":
    main()
