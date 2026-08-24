"""Report the under-identification detector's precision against human labels.

Precision on the adjudicated prefix is the honest statement of what the
detector is worth. Run after any adjudication session.

Usage:  python -m scripts.detector_precision
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

LABELS = Path("data/benchmark_v1_1_candidate/adjudication_labels.jsonl")


def main() -> None:
    if not LABELS.exists():
        print("no labels yet - run: python -m scripts.adjudicate")
        return
    rows = [json.loads(l) for l in open(LABELS, encoding="utf-8")]
    c = collections.Counter(r["label"] for r in rows)
    decided = c["keep"] + c["reject"]
    print(f"adjudicated: {len(rows)}  (keep {c['keep']}, reject {c['reject']}, unsure {c['unsure']})")
    if decided:
        p = c["reject"] / decided
        print(f"detector precision on adjudicated prefix: {p:.1%} "
              f"({c['reject']} true defects / {decided} decided)")
    # precision by rank band, to show whether the ranking carries signal
    bands = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if r["label"] == "unsure":
            continue
        b = r["rank"] // 50 * 50
        bands[b][0] += r["label"] == "reject"
        bands[b][1] += 1
    if len(bands) > 1:
        print("\nprecision by rank band (does the ranking carry signal?)")
        for b in sorted(bands):
            hit, tot = bands[b]
            print(f"  ranks {b:4d}-{b + 49:4d}: {hit}/{tot} = {hit / tot:.0%}" if tot else "")


if __name__ == "__main__":
    main()
