"""Build an archival sidecar for every source URL referenced by the benchmark.

The corpus snapshot used to build US-HealthBench v1.0 is not redistributed
(see DATASET_CARD.md). This script records the closest Wayback Machine
snapshot for each referenced source URL so that downstream users can inspect
the source text a benchmark item was derived from, even after the live page
changes or moves.

Writes data/benchmark_v1/source_archive.json. Does not modify frozen files.

Usage:  python -m scripts.build_wayback_sidecar
"""

from __future__ import annotations

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ITEMS = Path("data/benchmark_v1/benchmark_items.jsonl")
OUT = Path("data/benchmark_v1/source_archive.json")
WAYBACK = "https://archive.org/wayback/available?url="
TIMEOUT = 30


def referenced_sources() -> dict[str, dict]:
    """Map url -> {doc_id, agency, language} for every source in the benchmark."""
    sources: dict[str, dict] = {}
    with open(ITEMS, encoding="utf-8") as f:
        for line in f:
            for src in json.loads(line).get("source_documents") or []:
                sources.setdefault(
                    src["url"],
                    {
                        "doc_id": src["doc_id"],
                        "agency": src.get("agency"),
                        "language": src.get("language"),
                    },
                )
    return sources


def closest_snapshot(url: str, attempts: int = 3) -> dict | None:
    """Query the Wayback availability API, retrying with backoff.

    The API rate-limits under concurrency and returns an empty result rather
    than an error status when it throttles. Without retries roughly half of a
    296-URL sweep comes back as a spurious "not archived", so treat an empty
    response as retryable rather than authoritative.
    """
    for attempt in range(attempts):
        try:
            out = subprocess.run(
                ["curl", "-sS", "--max-time", str(TIMEOUT), WAYBACK + url],
                capture_output=True,
                text=True,
                timeout=TIMEOUT + 15,
            ).stdout
            snap = json.loads(out).get("archived_snapshots", {}).get("closest")
        except Exception:
            snap = None
        if snap:
            return {"timestamp": snap.get("timestamp"), "archive_url": snap.get("url")}
        if attempt < attempts - 1:
            time.sleep(1.5 * (attempt + 1))
    return None


def main() -> None:
    sources = referenced_sources()
    urls = list(sources)
    print(f"Querying Wayback for {len(urls)} referenced source URLs...")

    with ThreadPoolExecutor(4) as pool:
        snapshots = list(pool.map(closest_snapshot, urls))

    records = []
    for url, snap in zip(urls, snapshots):
        rec = {"url": url, **sources[url]}
        rec["archived"] = snap is not None
        if snap:
            rec["archive_timestamp"] = snap["timestamp"]
            rec["archive_url"] = snap["archive_url"]
        records.append(rec)

    records.sort(key=lambda r: r["doc_id"])
    n_arch = sum(r["archived"] for r in records)
    payload = {
        "description": (
            "Closest Wayback Machine snapshot for each source URL referenced by "
            "US-HealthBench v1.0. Generated post-freeze; does not alter benchmark items."
        ),
        "total_urls": len(records),
        "archived": n_arch,
        "not_archived": len(records) - n_arch,
        "sources": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  archived:     {n_arch}/{len(records)}")
    print(f"  not archived: {len(records) - n_arch}")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
