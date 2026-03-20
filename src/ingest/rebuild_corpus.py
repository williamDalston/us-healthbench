"""Rebuild the processed corpus from all raw HTML files in data/raw/."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def rebuild():
    """Re-parse and re-chunk everything from raw files."""
    from ..benchmark.chunker import chunk_document
    from .dedupe import deduplicate
    from .html_parser import clean_html_to_text

    # Load all metadata JSON files
    meta_files = sorted(RAW_DIR.glob("*.json"))
    meta_files = [f for f in meta_files if f.name != "_manifest.json"]

    docs = []
    for mf in meta_files:
        meta = json.loads(mf.read_text(encoding="utf-8"))
        doc_id = meta["doc_id"]
        html_path = RAW_DIR / f"{doc_id}.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")
        text = clean_html_to_text(html, preserve_headings=True)
        if len(text.strip()) < 200:
            continue
        meta["text"] = text
        docs.append(meta)

    logger.info("Parsed %d documents from raw files", len(docs))

    deduped = deduplicate(docs, text_key="text", id_key="doc_id", threshold=0.80)
    logger.info("After dedup: %d documents", len(deduped))

    # Chunk
    n_chunks = 0
    for doc in deduped:
        chunks = chunk_document(doc["doc_id"], doc["text"])
        doc["chunks"] = chunks
        n_chunks += len(chunks)
    logger.info("Created %d chunks", n_chunks)

    # Save
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    corpus_path = PROCESSED_DIR / "corpus.jsonl"
    with open(corpus_path, "w", encoding="utf-8") as f:
        for doc in deduped:
            out = {k: v for k, v in doc.items() if k != "text"}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    full_path = PROCESSED_DIR / "corpus_full.jsonl"
    with open(full_path, "w", encoding="utf-8") as f:
        for doc in deduped:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    # Stats
    from collections import Counter

    import numpy as np

    stats = {
        "total_documents": len(deduped),
        "total_chunks": n_chunks,
        "by_agency": dict(Counter(d["agency"] for d in deduped)),
        "by_language": dict(Counter(d.get("language", "en") for d in deduped)),
        "by_topic": dict(Counter(d.get("topic", "general") for d in deduped)),
    }
    chunk_counts = [len(d.get("chunks", [])) for d in deduped]
    if chunk_counts:
        stats["chunks_per_doc"] = {
            "mean": round(float(np.mean(chunk_counts)), 1),
            "median": round(float(np.median(chunk_counts)), 1),
            "min": int(np.min(chunk_counts)),
            "max": int(np.max(chunk_counts)),
        }
    (PROCESSED_DIR / "corpus_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

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

    return deduped


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    rebuild()
