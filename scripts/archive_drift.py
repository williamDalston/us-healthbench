"""Quantify drift between Wayback snapshots and the corpus collection date.

Condition-2 (with-sources) evaluation retrieves 2026 archive text, but the
gold answers were written from the corpus as collected on/before the v1.0
freeze. Where a page changed in between, the model is scored against a gold
it could not derive from what it was given.

Usage:  python -m scripts.archive_drift
"""

from __future__ import annotations

import collections
import json
from datetime import datetime
from pathlib import Path

ARCHIVE = Path("data/benchmark_v1/source_archive.json")
VERSION = Path("data/benchmark_v1/VERSION.json")
ITEMS = Path("data/benchmark_v1_1_candidate/clean_items.jsonl")
OUT = Path("data/benchmark_v1_1_candidate/archive_drift.json")

# Tolerance: a snapshot within this many days after the freeze is treated as
# contemporaneous. Federal guidance pages are not edited daily.
TOLERANCE_DAYS = 30


def main() -> None:
    freeze = datetime.fromisoformat(json.loads(VERSION.read_text())["created"]).replace(tzinfo=None)
    sources = json.loads(ARCHIVE.read_text())["sources"]
    by_url = {s["url"]: s for s in sources}

    items = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]

    status = {}
    for s in sources:
        if not s.get("archived"):
            status[s["url"]] = "no_snapshot"
            continue
        t = datetime.strptime(s["archive_timestamp"], "%Y%m%d%H%M%S")
        delta = (t - freeze).days
        if delta <= TOLERANCE_DAYS:
            status[s["url"]] = "contemporaneous"
        else:
            status[s["url"]] = "drifted"
        s["days_after_freeze"] = delta

    counts = collections.Counter(status.values())

    # item-level: an item is usable for condition 2 only if EVERY source it
    # cites has a contemporaneous snapshot.
    item_status = collections.Counter()
    usable_ids = []
    for it in items:
        st = {status.get(s.get("url"), "no_snapshot") for s in (it.get("source_documents") or [])}
        if not st:
            item_status["no_sources"] += 1
        elif "no_snapshot" in st:
            item_status["cites_unarchived"] += 1
        elif "drifted" in st:
            item_status["cites_drifted"] += 1
        else:
            item_status["fully_contemporaneous"] += 1
            usable_ids.append(it["item_id"])

    report = {
        "freeze_date": freeze.isoformat(),
        "tolerance_days": TOLERANCE_DAYS,
        "urls": dict(counts),
        "clean_subset_items": len(items),
        "items": dict(item_status),
        "condition2_usable_items": len(usable_ids),
        "drifted_examples": sorted(
            ({"url": s["url"], "days_after_freeze": s["days_after_freeze"]}
             for s in sources if status.get(s["url"]) == "drifted"),
            key=lambda x: -x["days_after_freeze"],
        )[:10],
    }
    OUT.write_text(json.dumps({**report, "usable_item_ids": usable_ids}, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
