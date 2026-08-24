"""Human adjudication of under-identification flags (defect class 5).

Shows one item at a time: the question, then its gold. You decide whether the
question identifies that gold. Keys:

    j = KEEP    the question does pick out this gold
    f = REJECT  under-identified; no system could derive this gold
    u = UNSURE
    b = back one item
    q = save and quit

Resumable: decisions are appended to adjudication_labels.jsonl and already
labelled items are skipped. Nothing is deleted; this only produces labels.

The queue is the relational detector's ranking (worst first). Because that
detector is triage-grade, these labels are also the ground truth used to report
its precision honestly -- see scripts/detector_precision.py.

Usage:  python -m scripts.adjudicate [--n 300]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ITEMS = Path("data/benchmark_v1_1_candidate/clean_items.jsonl")
FLAGS = Path("data/benchmark_v1_1_candidate/underspecified.json")
LABELS = Path("data/benchmark_v1_1_candidate/adjudication_labels.jsonl")

KEYS = {"j": "keep", "f": "reject", "u": "unsure"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    args = ap.parse_args()

    items = {json.loads(l)["item_id"]: json.loads(l) for l in open(ITEMS, encoding="utf-8")}
    queue = json.loads(FLAGS.read_text())["flagged_ids"][: args.n]

    done = {}
    if LABELS.exists():
        for l in open(LABELS, encoding="utf-8"):
            r = json.loads(l)
            done[r["item_id"]] = r["label"]

    todo = [i for i in queue if i not in done]
    print(f"queue {len(queue)}  labelled {len(done)}  remaining {len(todo)}\n")

    out = open(LABELS, "a", encoding="utf-8")
    idx = 0
    while idx < len(todo):
        iid = todo[idx]
        it = items[iid]
        ra = it.get("reference_answer") or {}
        print("=" * 72)
        print(f"[{idx + 1}/{len(todo)}]  {iid}   topic={it.get('topic')}  family={it.get('task_family')}")
        print(f"\nQUESTION:\n  {it['question']}")
        print(f"\nGOLD:\n  {(ra.get('answer_text') or '')[:420]}")
        pts = ra.get("required_points") or []
        if pts:
            print("\nREQUIRED POINTS:")
            for p in pts[:3]:
                print(f"  - {p[:110]}")
        print("\n  j=keep   f=reject(under-identified)   u=unsure   b=back   q=quit")
        try:
            k = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if k == "q":
            break
        if k == "b":
            idx = max(0, idx - 1)
            continue
        if k not in KEYS:
            continue
        out.write(json.dumps({
            "item_id": iid,
            "label": KEYS[k],
            "rank": queue.index(iid),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }) + "\n")
        out.flush()
        idx += 1

    out.close()
    n = sum(1 for _ in open(LABELS, encoding="utf-8")) if LABELS.exists() else 0
    print(f"\nsaved. {n} labels total in {LABELS}")


if __name__ == "__main__":
    main()
