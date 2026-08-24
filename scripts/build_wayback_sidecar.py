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
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ITEMS = Path("data/benchmark_v1/benchmark_items.jsonl")
OUT = Path(os.environ.get("WAYBACK_OUT", "data/benchmark_v1/source_archive.json"))
WAYBACK = "https://archive.org/wayback/available?url="
# Target the corpus collection window, not "now". Without an explicit
# timestamp the API returns the snapshot closest to the present day, which
# for a benchmark frozen in March 2026 means scoring against pages that may
# have been revised months after the gold answers were written.
TARGET_TIMESTAMP = os.environ.get("WAYBACK_TARGET", "20260320")
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


def closest_snapshot(url: str, attempts: int = 6) -> dict | None:
    """Query the Wayback availability API, retrying with backoff.

    Two distinct failure modes, both of which the API reports as something
    other than an error the caller would notice:

      * under concurrency it throttles with an HTTP 429 HTML body, which is
        not JSON at all;
      * it also returns a well-formed but empty result rather than an error.

    Both are retryable and neither means "no snapshot exists". A sweep that
    treats them as authoritative silently under-reports coverage by more than
    half. Raises on exhausted retries so the caller can record "unknown"
    rather than a false negative.
    """
    for attempt in range(attempts):
        try:
            out = subprocess.run(
                ["curl", "-sS", "--max-time", str(TIMEOUT),
                 f"{WAYBACK}{url}&timestamp={TARGET_TIMESTAMP}"],
                capture_output=True,
                text=True,
                timeout=TIMEOUT + 15,
            ).stdout
            if "429" in out[:200] and "<html" in out[:200].lower():
                raise RuntimeError("throttled")
            snap = json.loads(out).get("archived_snapshots", {}).get("closest")
        except RuntimeError:
            snap = None
        except Exception:
            snap = None
        if snap:
            return {"timestamp": snap.get("timestamp"), "archive_url": snap.get("url")}
        if attempt < attempts - 1:
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"no result after {attempts} attempts: {url}")


def main() -> None:
    sources = referenced_sources()
    urls = list(sources)
    print(f"Querying Wayback for {len(urls)} referenced source URLs...")

    snapshots = []
    for n, u in enumerate(urls, 1):
        try:
            snapshots.append(closest_snapshot(u))
        except RuntimeError:
            snapshots.append("unknown")
        if n % 25 == 0:
            print(f"  {n}/{len(urls)}", flush=True)
        time.sleep(float(os.environ.get("WAYBACK_DELAY", "1.0")))

    records = []
    for url, snap in zip(urls, snapshots):
        rec = {"url": url, **sources[url]}
        if snap == "unknown":
            rec["archived"] = None  # lookup failed; not evidence of absence
        else:
            rec["archived"] = snap is not None
        if snap and snap != "unknown":
            rec["archive_timestamp"] = snap["timestamp"]
            rec["archive_url"] = snap["archive_url"]
        records.append(rec)

    records.sort(key=lambda r: r["doc_id"])
    n_arch = sum(1 for r in records if r["archived"] is True)
    n_unknown = sum(1 for r in records if r["archived"] is None)
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
    print(f"  not archived: {sum(1 for r in records if r['archived'] is False)}")
    print(f"  lookup failed (unknown, NOT a negative): {n_unknown}")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
