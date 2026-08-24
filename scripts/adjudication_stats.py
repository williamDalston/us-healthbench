"""Precision, recall, prevalence, and self-agreement from the adjudication labels.

The control stratum is what makes recall and prevalence computable: without
unflagged items in the queue there is no way to know what the detector missed.

Prevalence is a stratified estimate. The two strata are sampled at very
different rates (300 of ~525 flagged, 50 of ~533 unflagged), so a raw rate over
the labelled items would be badly biased toward the flagged stratum.

Intervals are Wilson score intervals at 95%.

Usage:  python -m scripts.adjudication_stats
"""

from __future__ import annotations

import json
import math
from pathlib import Path

QUEUE = Path("data/benchmark_v1_1_candidate/adjudication_queue.json")
LABELS = Path("data/benchmark_v1_1_candidate/adjudication_labels.jsonl")
RELABELS = Path("data/benchmark_v1_1_candidate/adjudication_relabels.jsonl")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return {json.loads(l)["item_id"]: json.loads(l)["label"]
            for l in open(path, encoding="utf-8")}


def main() -> None:
    q = json.loads(QUEUE.read_text())
    stratum = {r["item_id"]: r["stratum"] for r in q["queue"]}
    labels = load(LABELS)
    if not labels:
        print("no labels yet - run: python -m scripts.adjudicate")
        return

    fl = {i: v for i, v in labels.items() if stratum.get(i) == "flagged"}
    ct = {i: v for i, v in labels.items() if stratum.get(i) == "control"}

    tp = sum(1 for v in fl.values() if v == "reject")
    fp = len(fl) - tp
    fn = sum(1 for v in ct.values() if v == "reject")
    tn = len(ct) - fn

    print(f"labelled {len(labels)} of {len(q['queue'])}  "
          f"(flagged {len(fl)}/{q['sampled_flagged']}, control {len(ct)}/{q['sampled_control']})")

    if fl:
        lo, hi = wilson(tp, len(fl))
        print(f"\nprecision  {tp}/{len(fl)} = {tp/len(fl):.1%}   95% CI [{lo:.1%}, {hi:.1%}]")
    if ct:
        lo, hi = wilson(fn, len(ct))
        print(f"defect rate among UNflagged  {fn}/{len(ct)} = {fn/len(ct):.1%}   "
              f"95% CI [{lo:.1%}, {hi:.1%}]")

    # stratified prevalence over the whole 1,058-item subset
    NF, NU = q["n_flagged_total"], q["n_unflagged_total"]
    if fl and ct:
        pf, pu = tp / len(fl), fn / len(ct)
        N = NF + NU
        prev = (NF * pf + NU * pu) / N
        # variance of a stratified mean
        vf = pf * (1 - pf) / len(fl)
        vu = pu * (1 - pu) / len(ct)
        se = math.sqrt(((NF / N) ** 2) * vf + ((NU / N) ** 2) * vu)
        print(f"\nstratified prevalence over {N} items: {prev:.1%}  "
              f"95% CI [{max(0, prev - 1.96 * se):.1%}, {min(1, prev + 1.96 * se):.1%}]")
        est_missed = NU * pu
        print(f"estimated defective items the detector MISSED: {est_missed:.0f}")
        if tp + est_missed > 0:
            print(f"recall {NF * pf / (NF * pf + est_missed):.1%}")

    # self-agreement
    re = load(RELABELS)
    both = [i for i in re if i in labels]
    if both:
        agree = sum(1 for i in both if re[i] == labels[i])
        po = agree / len(both)
        # Cohen's kappa against chance agreement of the two passes
        def rate(d, ids):
            return sum(1 for i in ids if d[i] == "reject") / len(ids)
        p1, p2 = rate(labels, both), rate(re, both)
        pe = p1 * p2 + (1 - p1) * (1 - p2)
        kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
        print(f"\nself-agreement on {len(both)} re-labelled: {po:.1%}  kappa {kappa:.2f}")
    else:
        print("\nself-agreement: not yet measured "
              "(run `python -m scripts.adjudicate --reliability` a few days later)")


if __name__ == "__main__":
    main()
