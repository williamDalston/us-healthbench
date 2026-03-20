"""Semantic chunking of source documents for the benchmark corpus."""

import logging
import re

logger = logging.getLogger(__name__)

# Chunking parameters
MIN_CHUNK_TOKENS = 50
MAX_CHUNK_TOKENS = 500
TARGET_CHUNK_TOKENS = 250
HEADING_PATTERN = re.compile(r"^\[h[1-6]\]\s+", re.MULTILINE)


def estimate_tokens(text):
    # rough estimate: words * 1.3, works okay for English
    return int(len(text.split()) * 1.3)


def split_by_headings(text: str) -> list[dict]:
    """
    Split text into sections based on heading markers ([h1], [h2], etc.)
    inserted by the HTML parser.
    """
    sections: list[dict] = []
    current_title = "Introduction"
    current_level = 0
    current_lines: list[str] = []

    for line in text.split("\n"):
        heading_match = re.match(r"^\[h(\d)\]\s+(.+)$", line.strip())
        if heading_match:
            # Save previous section
            if current_lines:
                section_text = "\n".join(current_lines).strip()
                if section_text:
                    sections.append(
                        {
                            "section_title": current_title,
                            "level": current_level,
                            "text": section_text,
                        }
                    )
            current_level = int(heading_match.group(1))
            current_title = heading_match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Last section
    if current_lines:
        section_text = "\n".join(current_lines).strip()
        if section_text:
            sections.append(
                {
                    "section_title": current_title,
                    "level": current_level,
                    "text": section_text,
                }
            )

    return sections


# TODO: add support for more languages (token multiplier differs for es)
def chunk_section(
    section_text: str,
    section_title: str,
    max_tokens: int = MAX_CHUNK_TOKENS,
    min_tokens: int = MIN_CHUNK_TOKENS,
) -> list[dict]:
    """Split a section into chunks that respect paragraph boundaries.

    Tries to keep chunks between min_tokens and max_tokens.
    Splits on paragraph boundaries first, then sentences if needed.
    """
    paragraphs = [p.strip() for p in section_text.split("\n\n") if p.strip()]

    chunks: list[dict] = []
    cur_chunk: list[str] = []
    cur_toks = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If a single paragraph exceeds max, split on sentences
        if para_tokens > max_tokens:
            # Flush current chunk first
            if cur_chunk:
                chunks.append(
                    {
                        "section_title": section_title,
                        "text": "\n\n".join(cur_chunk),
                    }
                )
                cur_chunk = []
                cur_toks = 0

            # Split paragraph into sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            sent_chunk: list[str] = []
            sent_tokens = 0
            for sent in sentences:
                st = estimate_tokens(sent)
                if sent_tokens + st > max_tokens and sent_chunk:
                    chunks.append(
                        {
                            "section_title": section_title,
                            "text": " ".join(sent_chunk),
                        }
                    )
                    sent_chunk = []
                    sent_tokens = 0
                sent_chunk.append(sent)
                sent_tokens += st
            if sent_chunk:
                chunks.append(
                    {
                        "section_title": section_title,
                        "text": " ".join(sent_chunk),
                    }
                )
            continue

        # Normal case: accumulate paragraphs
        if cur_toks + para_tokens > max_tokens and cur_chunk:
            chunks.append(
                {
                    "section_title": section_title,
                    "text": "\n\n".join(cur_chunk),
                }
            )
            cur_chunk = []
            cur_toks = 0

        cur_chunk.append(para)
        cur_toks += para_tokens

    # Flush remaining
    if cur_chunk:
        chunks.append(
            {
                "section_title": section_title,
                "text": "\n\n".join(cur_chunk),
            }
        )

    # Merge undersized chunks with neighbors
    merged: list[dict] = []
    for ch in chunks:
        if merged and estimate_tokens(ch["text"]) < min_tokens:
            merged[-1]["text"] += "\n\n" + ch["text"]
        else:
            merged.append(ch)

    return merged


def chunk_document(
    doc_id: str,
    text: str,
    max_tokens: int = MAX_CHUNK_TOKENS,
    min_tokens: int = MIN_CHUNK_TOKENS,
) -> list[dict]:
    """Chunk a full document into labeled pieces with IDs and offsets."""
    sections = split_by_headings(text)
    if not sections:
        # No headings found -- treat entire text as one section
        sections = [{"section_title": "Content", "level": 0, "text": text}]

    all_chunks: list[dict] = []
    chunk_seq = 0

    for section in sections:
        section_chunks = chunk_section(
            section["text"],
            section["section_title"],
            max_tokens=max_tokens,
            min_tokens=min_tokens,
        )

        for chunk in section_chunks:
            chunk_seq += 1
            chunk_id = f"{doc_id}_c{chunk_seq:02d}"

            # Find character offsets in the original text
            start = text.find(chunk["text"][:50])
            end = start + len(chunk["text"]) if start >= 0 else -1
            # print(f"  chunk {chunk_id}: start={start}, end={end}")

            all_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "section_title": chunk["section_title"],
                    "text": chunk["text"],
                    "char_offset_start": max(start, 0),
                    "char_offset_end": max(end, 0),
                    "token_count": estimate_tokens(chunk["text"]),
                }
            )

    logger.info("Chunked %s into %d chunks", doc_id, len(all_chunks))
    return all_chunks
