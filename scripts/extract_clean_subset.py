"""Extract the v1.1-candidate clean subset from the frozen v1.0 benchmark.

Removes all four audited defect classes (docs/DATA_QUALITY.md):
  1. encoding corruption (mojibake)
  2. template splice artifacts
  3. duplicate questions with conflicting golds (all copies dropped;
     benign exact duplicates collapsed to one)
  4. items derived from administrative (polluted) source documents

Writes data/benchmark_v1_1_candidate/clean_items.jsonl + stats.json.
The v1.0 freeze is untouched. This output is a CANDIDATE: it does not
become v1.1 until the human spot-check required by the protocol is done.

Usage:  python -m scripts.extract_clean_subset
"""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

from scripts.audit_data_quality import ADMIN, MOJIBAKE, item_texts, load

OUT_DIR = Path("data/benchmark_v1_1_candidate")


def main() -> None:
    items = load()

    byq = collections.defaultdict(list)
    for it in items:
        byq[it["question"].strip()].append(it)
    conflicting = {
        q for q, v in byq.items() if len(v) > 1
        and len({(i.get("reference_answer") or {}).get("answer_text", "") for i in v}) > 1
    }

    def clean(it):
        if any(MOJIBAKE.search(t or "") for t in item_texts(it)):
            return False
        q = it["question"].rstrip()
        if q.endswith(":?") or "??" in it["question"]:
            return False
        if it["question"].strip() in conflicting:
            return False
        if any(ADMIN.search(s.get("url", "")) for s in (it.get("source_documents") or [])):
            return False
        return True

    seen, uniq = set(), []
    for it in items:
        if not clean(it):
            continue
        k = it["question"].strip()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(it)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "clean_items.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for it in uniq:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    stats = {
        "source": "data/benchmark_v1/benchmark_items.jsonl (frozen v1.0)",
        "items": len(uniq),
        "of_v1_items": len(items),
        "by_language": dict(collections.Counter(i["language"] for i in uniq)),
        "by_task_family": dict(collections.Counter(i["task_family"] for i in uniq)),
        "by_difficulty": dict(collections.Counter(i.get("difficulty") for i in uniq)),
        "sha256": sha,
        "status": "candidate — pending human spot-check",
    }
    (OUT_DIR / "stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
