"""Detect a fifth defect class: questions that do not identify their own gold.

Template collision (v1.0 class 3) catches *identical* question strings carrying
different golds. It cannot catch a question that is merely too generic for its
gold -- e.g. "What are the key facts about symptoms and stages?" paired with a
gold about Lyme disease. Nothing is duplicated, so collision detection is blind
to it, yet the item is unanswerable as posed: no system could derive that gold
from that question.

Lexical question/gold overlap is NOT a usable detector for this -- it flags
legitimate items whose gold simply uses different words (33.6% flagged, mostly
false positives on inspection).

The principled test is relational, in the spirit of the collision finding:
a question identifies its gold if its OWN gold ranks above other items' golds.
If dozens of other golds match the question at least as well, the question does
not pick out its answer, and scoring against it measures nothing.

Usage:  python -m scripts.detect_underspecified
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ITEMS = Path("data/benchmark_v1_1_candidate/clean_items.jsonl")
OUT = Path("data/benchmark_v1_1_candidate/underspecified.json")

STOP = set("""what should i take steps regarding do about my the a an for and or of to is
are can how when where who why need know does official guidance say key facts according
health u.s us summarize you concerned please tell me there any this that with from""".split())

# A question is under-identified if at least this many OTHER items' golds match
# it as well as, or better than, its own.
RIVAL_THRESHOLD = 10


def toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", (s or "").lower())} - STOP


def gold_text(it: dict) -> str:
    ra = it.get("reference_answer") or {}
    return " ".join([ra.get("answer_text", "")] + (ra.get("required_points") or []))


def main() -> None:
    items = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]
    q = [toks(it["question"]) for it in items]
    g = [toks(gold_text(it)) for it in items]

    def sim(a: set, b: set) -> float:
        return len(a & b) / len(a) if a else 0.0

    # Adversarial items are exempt by design: their gold is a safety refusal
    # ("this requires personalized medical advice"), which shares no vocabulary
    # with the question on purpose. Low overlap there is the intended behaviour,
    # not a defect, so including them would flag correct items.
    flagged = []
    for i, it in enumerate(items):
        if not q[i] or (it.get("flags") or {}).get("adversarial"):
            continue
        own = sim(q[i], g[i])
        rivals = sum(1 for j in range(len(items)) if j != i and sim(q[i], g[j]) >= own)
        if rivals >= RIVAL_THRESHOLD:
            flagged.append({
                "item_id": it["item_id"],
                "question": it["question"][:120],
                "own_gold_score": round(own, 3),
                "rival_golds_scoring_at_least_as_well": rivals,
            })

    flagged.sort(key=lambda r: -r["rival_golds_scoring_at_least_as_well"])
    report = {
        "method": "relational: count other items' golds matching this question >= its own gold",
        "rival_threshold": RIVAL_THRESHOLD,
        "items": len(items),
        "adversarial_exempt": sum(1 for it in items if (it.get("flags") or {}).get("adversarial")),
        "flagged": len(flagged),
        "pct": round(100 * len(flagged) / len(items), 1),
        "worst": flagged[:15],
    }
    OUT.write_text(json.dumps({**report, "flagged_ids": [f["item_id"] for f in flagged]}, indent=2) + "\n")
    print(json.dumps(report, indent=2)[:2600])


if __name__ == "__main__":
    main()
