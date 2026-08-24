"""Adjudicate under-identification (defect class 5). A chore, not a research task.

=============================================================================
DECISION RULE -- fixed 2026-08-24, BEFORE any item was seen. Do not amend it
mid-pass; an amended criterion turns labels into impressions.

    Could a competent reader, given ONLY the question, have produced this gold?

    y = yes, the question identifies this gold  -> KEEP
    n = no                                      -> REJECT (under-identified)

Nothing about whether the gold is good, accurate, well-written, or useful.
Nothing about whether the question is well-phrased. One question only.
=============================================================================

Binary. No notes field, no going back, no skipping -- each of those multiplies
the time per item and none improves the label.

The queue is blinded: flagged and control items are shuffled together and the
stratum is never displayed. Sessions are capped (default 100) because the last
items of a long sitting are systematically sloppier than the first. Three
sittings, not one.

Resumable. Append-only. Nothing is deleted and no item is ever modified.

Usage:
  python -m scripts.adjudicate                # next 100
  python -m scripts.adjudicate --n 50
  python -m scripts.adjudicate --reliability  # re-label 30 already done, blind
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ITEMS = Path("data/benchmark_v1_1_candidate/clean_items.jsonl")
QUEUE = Path("data/benchmark_v1_1_candidate/adjudication_queue.json")
LABELS = Path("data/benchmark_v1_1_candidate/adjudication_labels.jsonl")
RELABELS = Path("data/benchmark_v1_1_candidate/adjudication_relabels.jsonl")


def load_labels(path: Path) -> dict:
    if not path.exists():
        return {}
    return {json.loads(l)["item_id"]: json.loads(l)["label"]
            for l in open(path, encoding="utf-8")}


def ask(it: dict, n: int, total: int) -> str | None:
    ra = it.get("reference_answer") or {}
    print("\n" + "=" * 72)
    print(f"[{n}/{total}]")
    print(f"\nQUESTION\n  {it['question']}")
    print(f"\nGOLD\n  {(ra.get('answer_text') or '')[:400]}")
    for p in (ra.get("required_points") or [])[:3]:
        print(f"  - {p[:110]}")
    print("\n  Could a reader given ONLY the question have produced this gold?")
    while True:
        try:
            k = input("  y / n  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if k in ("y", "n"):
            return "keep" if k == "y" else "reject"
        if k == "q":
            return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--reliability", action="store_true",
                    help="re-label 30 already-adjudicated items, prior calls hidden")
    args = ap.parse_args()

    items = {json.loads(l)["item_id"]: json.loads(l) for l in open(ITEMS, encoding="utf-8")}
    queue = json.loads(QUEUE.read_text())["queue"]
    done = load_labels(LABELS)

    if args.reliability:
        already = load_labels(RELABELS)
        pool = [q for q in queue if q["item_id"] in done and q["item_id"] not in already]
        random.Random(99).shuffle(pool)
        todo, out_path = pool[:30], RELABELS
        print(f"RELIABILITY PASS: {len(todo)} items, your earlier calls are not shown.")
    else:
        todo = [q for q in queue if q["item_id"] not in done][: args.n]
        out_path = LABELS
        print(f"queue {len(queue)}  labelled {len(done)}  this sitting {len(todo)}")

    if not todo:
        print("nothing to do")
        return

    with open(out_path, "a", encoding="utf-8") as f:
        for n, q in enumerate(todo, 1):
            label = ask(items[q["item_id"]], n, len(todo))
            if label is None:
                print("\nstopped early - progress saved")
                break
            f.write(json.dumps({
                "item_id": q["item_id"],
                "label": label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }) + "\n")
            f.flush()

    total = len(load_labels(out_path))
    print(f"\nsaved. {total} labels in {out_path.name}")
    print("next: python -m scripts.adjudication_stats")


if __name__ == "__main__":
    main()
