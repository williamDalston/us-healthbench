"""Matched comparison of two systems on the items they BOTH answered.

Unmatched means are not comparable: item mix alone moves several dimensions
(abstention items score source_support=2 for citing nothing), so a difference
between two different samples says nothing about the systems.

Usage:  python -m scripts.compare_systems claude_norag qwen3_norag
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

D = Path("data/experiment_v1_1")
DIMS = ["factual_correctness", "source_support", "safety",
        "uncertainty_handling", "clarity"]


def load(sysname):
    return {json.loads(l)["item_id"]: json.loads(l)
            for l in open(D / f"eval_{sysname}.jsonl", encoding="utf-8")}


def main() -> None:
    a_name, b_name = sys.argv[1], sys.argv[2]
    a, b = load(a_name), load(b_name)
    shared = sorted(set(a) & set(b))
    print(f"{a_name}: {len(a)} items   {b_name}: {len(b)} items   matched: {len(shared)}\n")
    if not shared:
        print("no shared items - nothing comparable")
        return

    print(f"{'dimension':24s} {a_name:>16s} {b_name:>16s} {'diff':>8s}  {'wins a/b/tie':>14s}")
    for d in DIMS:
        av = [a[i]["scores"][d] for i in shared]
        bv = [b[i]["scores"][d] for i in shared]
        ma, mb = sum(av) / len(av), sum(bv) / len(bv)
        wa = sum(1 for x, y in zip(av, bv) if x > y)
        wb = sum(1 for x, y in zip(av, bv) if y > x)
        tie = len(shared) - wa - wb
        flag = "  (floored)" if d == "source_support" else ""
        print(f"{d:24s} {ma:16.2f} {mb:16.2f} {ma-mb:+8.2f}  {wa:4d}/{wb:d}/{tie:d}{flag}")

    # abstention items distort source_support; report the split
    absten = [i for i in shared if a[i]["scores"]["source_support"] == 2
              or b[i]["scores"]["source_support"] == 2]
    print(f"\nitems where either system scored source_support=2: {len(absten)} of {len(shared)}")
    print("(these are abstention items with no expected chunks; the scorer awards")
    print(" full credit for citing nothing, so this dimension is not comparable)")

    for d in ["factual_correctness", "safety"]:
        worst = sorted(shared, key=lambda i: a[i]["scores"][d] + b[i]["scores"][d])[:3]
        print(f"\nlowest combined {d}: {worst}")


if __name__ == "__main__":
    main()
