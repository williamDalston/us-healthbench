"""Day 2 Pipeline: Collect -> Parse -> Chunk -> Deduplicate -> Save corpus.

Usage:
    python -m src.ingest.pipeline [--max-pages N] [--agencies CDC,NIH,...]
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def run_pipeline(
    max_pages_per_agency: int = 80,
    max_crawl_depth: int = 2,
    agencies: list[str] | None = None,
):
    """Run the full Day 2 ingestion pipeline."""

    # Step 1 - collect
    logger.info("=" * 60)
    logger.info("STEP 1: Collecting source documents")
    logger.info("=" * 60)
    from .source_collector import collect_sources

    docs = collect_sources(
        output_dir=RAW_DIR,
        agencies=agencies,
        max_pages_per_agency=max_pages_per_agency,
        max_crawl_depth=max_crawl_depth,
    )
    logger.info("Collected %d raw documents", len(docs))

    # Step 2 - parse HTML
    logger.info("=" * 60)
    logger.info("STEP 2: Parsing HTML to clean text")
    logger.info("=" * 60)
    from .html_parser import clean_html_to_text

    parsed_docs: list[dict] = []
    for doc in docs:
        html = doc.raw_html or ""
        if not html:
            # Try loading from file
            html_path = RAW_DIR / f"{doc.doc_id}.html"
            if html_path.exists():
                html = html_path.read_text(encoding="utf-8")

        text = clean_html_to_text(html, preserve_headings=True)
        if len(text.strip()) < 200:
            logger.debug("Skipping %s — parsed text too short (%d chars)", doc.doc_id, len(text))
            continue

        parsed_doc = doc.to_metadata()
        parsed_doc["text"] = text
        parsed_docs.append(parsed_doc)

    logger.info(
        "Parsed %d documents (dropped %d short/empty)",
        len(parsed_docs),
        len(docs) - len(parsed_docs),
    )
    # print(f"parsed {len(parsed_docs)} documents")

    # --- deduplicate ---
    logger.info("=" * 60)
    logger.info("STEP 3: Deduplicating corpus")
    logger.info("=" * 60)
    from .dedupe import deduplicate

    deduped_docs = deduplicate(parsed_docs, text_key="text", id_key="doc_id", threshold=0.80)
    logger.info("After dedup: %d documents", len(deduped_docs))

    # Step 4: chunk
    logger.info("=" * 60)
    logger.info("STEP 4: Chunking documents")
    logger.info("=" * 60)
    from ..benchmark.chunker import chunk_document

    total_chunks = 0
    for doc in deduped_docs:
        chunks = chunk_document(doc["doc_id"], doc["text"])
        doc["chunks"] = chunks
        total_chunks += len(chunks)

    logger.info(
        "Created %d chunks across %d documents (avg %.1f chunks/doc)",
        total_chunks,
        len(deduped_docs),
        total_chunks / max(len(deduped_docs), 1),
    )

    # save processed corpus
    logger.info("=" * 60)
    logger.info("STEP 5: Saving processed corpus")
    logger.info("=" * 60)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Save full corpus as JSONL (one doc per line, with chunks)
    corpus_path = PROCESSED_DIR / "corpus.jsonl"
    with open(corpus_path, "w", encoding="utf-8") as f:
        for doc in deduped_docs:
            # Don't include full text in JSONL — just metadata + chunks
            out = {k: v for k, v in doc.items() if k != "text"}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    logger.info("Saved corpus to %s", corpus_path)

    # Save full docs with text (for item generation)
    full_corpus_path = PROCESSED_DIR / "corpus_full.jsonl"
    with open(full_corpus_path, "w", encoding="utf-8") as f:
        for doc in deduped_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    logger.info("Saved full corpus to %s", full_corpus_path)

    # TODO: add per-agency stats breakdown to the log output
    logger.info("=" * 60)
    logger.info("CORPUS STATISTICS")
    logger.info("=" * 60)
    stats = compute_corpus_stats(deduped_docs)
    stats_path = PROCESSED_DIR / "corpus_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print_stats(stats)

    return deduped_docs


def compute_corpus_stats(docs) -> dict:
    """Compute summary statistics for the corpus."""
    from collections import Counter

    stats = {
        "total_documents": len(docs),
        "total_chunks": sum(len(d.get("chunks", [])) for d in docs),
        "by_agency": dict(Counter(d["agency"] for d in docs)),
        "by_language": dict(Counter(d.get("language", "en") for d in docs)),
        "by_topic": dict(Counter(d.get("topic", "general") for d in docs)),
        "by_content_type": dict(Counter(d.get("content_type", "webpage") for d in docs)),
    }

    # Chunk stats
    chunk_counts = [len(d.get("chunks", [])) for d in docs]
    if chunk_counts:
        import numpy as np

        stats["chunks_per_doc"] = {
            "mean": round(float(np.mean(chunk_counts)), 1),
            "median": round(float(np.median(chunk_counts)), 1),
            "min": int(np.min(chunk_counts)),
            "max": int(np.max(chunk_counts)),
        }

    return stats


def print_stats(stats):
    # just dump stats to console
    print(f"\n  Total documents:  {stats['total_documents']}")
    print(f"  Total chunks:     {stats['total_chunks']}")
    print("\n  By agency:")
    for k, v in sorted(stats["by_agency"].items()):
        print(f"    {k:6s}  {v:4d}")
    print("\n  By language:")
    for k, v in sorted(stats["by_language"].items()):
        print(f"    {k:6s}  {v:4d}")
    print("\n  By topic:")
    for k, v in sorted(stats["by_topic"].items(), key=lambda x: -x[1]):
        print(f"    {k:28s}  {v:4d}")
    if "chunks_per_doc" in stats:
        cpd = stats["chunks_per_doc"]
        print(
            f"\n  Chunks/doc:  mean={cpd['mean']}, median={cpd['median']}, "
            f"min={cpd['min']}, max={cpd['max']}"
        )
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="US-HealthBench corpus ingestion pipeline")
    parser.add_argument(
        "--max-pages", type=int, default=80, help="Max pages per agency (default: 80)"
    )
    parser.add_argument(
        "--depth", type=int, default=2, help="Max crawl depth from seed pages (default: 2)"
    )
    parser.add_argument(
        "--agencies", type=str, default=None, help="Comma-separated agency codes (default: all)"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    agency_list = args.agencies.split(",") if args.agencies else None
    run_pipeline(
        max_pages_per_agency=args.max_pages,
        max_crawl_depth=args.depth,
        agencies=agency_list,
    )
