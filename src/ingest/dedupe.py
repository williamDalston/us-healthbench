"""Near-duplicate detection and deduplication for corpus documents."""

import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def text_fingerprint(text):
    # sha256 of normalized (lowered, whitespace-collapsed) text
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def shingle_set(text, k=5):
    # k-shingle (k-gram) set for similarity comparison
    words = text.lower().split()
    if len(words) < k:
        return {" ".join(words)}
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def jaccard_similarity(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def find_near_duplicates(
    documents: list[dict],
    text_key: str = "text",
    id_key: str = "doc_id",
    threshold: float = 0.85,
    shingle_k: int = 5,
) -> list[tuple[str, str, float]]:
    """Find near-duplicate pairs using Jaccard similarity on k-shingles.

    Returns list of (doc_id_a, doc_id_b, similarity) tuples.
    """
    # FIXME: O(n^2) comparison -- should use minhash/LSH for larger corpora
    shingles: dict[str, set[str]] = {}
    for doc in documents:
        doc_id = doc[id_key]
        text = doc.get(text_key, "")
        shingles[doc_id] = shingle_set(text, k=shingle_k)

    doc_ids = list(shingles.keys())
    duplicates: list[tuple[str, str, float]] = []

    for i in range(len(doc_ids)):
        for j in range(i + 1, len(doc_ids)):
            sim = jaccard_similarity(shingles[doc_ids[i]], shingles[doc_ids[j]])
            if sim >= threshold:
                duplicates.append((doc_ids[i], doc_ids[j], sim))
                logger.info(
                    "Near-duplicate: %s <-> %s (similarity=%.3f)",
                    doc_ids[i],
                    doc_ids[j],
                    sim,
                )

    return duplicates


def find_exact_duplicates(
    documents: list[dict],
    text_key: str = "text",
    id_key: str = "doc_id",
) -> dict[str, list[str]]:
    """Find exact duplicate documents by text fingerprint.

    Returns dict mapping fingerprint -> list of doc_ids sharing it.
    Only includes fingerprints with 2+ documents.
    """
    fingerprint_groups: dict[str, list[str]] = defaultdict(list)

    for doc in documents:
        fp = text_fingerprint(doc.get(text_key, ""))
        fingerprint_groups[fp].append(doc[id_key])

    return {fp: ids for fp, ids in fingerprint_groups.items() if len(ids) > 1}


def deduplicate(
    documents: list[dict],
    text_key: str = "text",
    id_key: str = "doc_id",
    threshold: float = 0.85,
    prefer_longer: bool = True,
) -> list[dict]:
    """Remove near-duplicate and exact-duplicate documents.
    Keeps the longer doc when duplicates are found (unless prefer_longer=False)."""

    # First pass: exact duplicates
    exact_dupes = find_exact_duplicates(documents, text_key, id_key)
    exact_remove: set[str] = set()
    for _fp, ids in exact_dupes.items():
        # Keep the first, remove the rest
        for doc_id in ids[1:]:
            exact_remove.add(doc_id)
            logger.info("Removing exact duplicate: %s", doc_id)

    filtered = [d for d in documents if d[id_key] not in exact_remove]

    # Second pass: near-duplicates
    near_dupes = find_near_duplicates(filtered, text_key, id_key, threshold)
    near_remove: set[str] = set()
    doc_by_id = {d[id_key]: d for d in filtered}

    for id_a, id_b, sim in near_dupes:
        if id_a in near_remove or id_b in near_remove:
            continue
        if prefer_longer:
            len_a = len(doc_by_id[id_a].get(text_key, ""))
            len_b = len(doc_by_id[id_b].get(text_key, ""))
            remove = id_b if len_a >= len_b else id_a
        else:
            remove = id_b
        near_remove.add(remove)
        logger.info(
            "Removing near-duplicate: %s (sim=%.3f with %s)",
            remove,
            sim,
            id_a if remove == id_b else id_b,
        )

    result = [d for d in filtered if d[id_key] not in near_remove]
    logger.info(
        "Deduplication: %d -> %d documents (%d exact, %d near-duplicates removed)",
        len(documents),
        len(result),
        len(exact_remove),
        len(near_remove),
    )
    return result
