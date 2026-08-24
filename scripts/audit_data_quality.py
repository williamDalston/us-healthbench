"""Audit known defect classes in the frozen v1.0 benchmark.

Read-only. Recomputes every figure quoted in docs/DATA_QUALITY.md so the
disclosure can be re-derived from the frozen file rather than trusted.

Usage:  python -m scripts.audit_data_quality
"""

from __future__ import annotations

import collections
import json
import re
from pathlib import Path

ITEMS = Path("data/benchmark_v1/benchmark_items.jsonl")
PAIRS = Path("data/benchmark_v1/cross_language_pairs.json")

# Signatures of UTF-8 text decoded as Latin-1 and re-encoded (double encoding).
MOJIBAKE = re.compile(r"Ã|Â|â€|ã©|ã³|ã±|Ã¡|Ã©|Ã­|Ã³|Ãº|Ã±|â¿|ã¿", re.I)


def load():
    return [json.loads(line) for line in open(ITEMS, encoding="utf-8")]


def item_texts(it):
    yield it.get("question", "")
    ra = it.get("reference_answer") or {}
    yield ra.get("answer_text", "")
    yield from (ra.get("required_points") or [])
    for src in it.get("source_documents") or []:
        yield src.get("title") or ""


def main() -> None:
    items = load()
    n = len(items)
    print(f"items: {n}\n")

    mojibake = [i for i in items if any(MOJIBAKE.search(t or "") for t in item_texts(i))]
    by_lang = collections.Counter(i["language"] for i in mojibake)
    lang_totals = collections.Counter(i["language"] for i in items)
    print("1. ENCODING CORRUPTION")
    print(f"   items with double-encoded UTF-8: {len(mojibake)} ({100*len(mojibake)/n:.1f}%)")
    for lang in sorted(by_lang):
        print(f"     {lang}: {by_lang[lang]} of {lang_totals[lang]} ({100*by_lang[lang]/lang_totals[lang]:.1f}% of that language)")

    garbled = [i for i in items if i["question"].rstrip().endswith(":?") or "??" in i["question"]]
    print(f"\n2. TEMPLATE SPLICE ARTIFACTS")
    print(f"   questions ending ':?' or containing '??': {len(garbled)}")

    byq = collections.defaultdict(list)
    for i in items:
        byq[i["question"].strip()].append(i)
    dupes = {q: v for q, v in byq.items() if len(v) > 1}
    conflicting = {
        q: v for q, v in dupes.items()
        if len({(i.get("reference_answer") or {}).get("answer_text", "") for i in v}) > 1
    }
    n_dupe_items = sum(len(v) for v in dupes.values())
    n_conf_items = sum(len(v) for v in conflicting.values())
    worst_q, worst_v = max(dupes.items(), key=lambda kv: len(kv[1]))
    print(f"\n3. DUPLICATE QUESTIONS WITH CONFLICTING GOLD ANSWERS")
    print(f"   distinct question strings: {len(byq)} across {n} items")
    print(f"   repeated question texts: {len(dupes)}, spanning {n_dupe_items} items ({100*n_dupe_items/n:.1f}%)")
    print(f"   repeated questions with differing gold answers: {len(conflicting)}")
    print(f"   items affected by a conflicting duplicate: {n_conf_items} ({100*n_conf_items/n:.1f}%)")
    print(f"   most-repeated question appears {len(worst_v)}x: {worst_q[:70]}...")

    pairs = json.loads(PAIRS.read_text(encoding="utf-8"))
    lang = {i["item_id"]: i.get("language") for i in items}
    swapped = sum(1 for p in pairs if lang.get(p.get("en_item_id")) == "es")
    unverified = sum(1 for p in pairs if p.get("semantic_equivalence_verified") is False)
    print(f"\n4. CROSS-LANGUAGE PAIR LABELS")
    print(f"   pairs: {len(pairs)}")
    print(f"   pairs with en_item_id/es_item_id swapped: {swapped} ({100*swapped/len(pairs):.0f}%)")
    print(f"   pairs with semantic_equivalence_verified == false: {unverified}")

    def clean(it):
        if any(MOJIBAKE.search(t or "") for t in item_texts(it)):
            return False
        q = it["question"].rstrip()
        return not (q.endswith(":?") or "??" in q)

    conf_q = set(conflicting)
    survivors = [i for i in items if clean(i) and i["question"].strip() not in conf_q]
    seen, uniq = set(), []
    for i in survivors:
        k = i["question"].strip()
        if k not in seen:
            seen.add(k)
            uniq.append(i)
    print(f"\n5. RECOVERABLE SUBSET (defect classes 1-3 removed, exact duplicates collapsed)")
    print(f"   items: {len(uniq)} of {n} ({100*len(uniq)/n:.1f}%)")
    print(f"   by language: {dict(collections.Counter(i['language'] for i in uniq))}")
    print(f"   by task family: {dict(collections.Counter(i['task_family'] for i in uniq))}")


if __name__ == "__main__":
    main()
