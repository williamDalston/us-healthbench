"""Parse PDF documents from agency sources into clean text."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_path: str | Path):
    """Extract text from a PDF using pdfplumber. Returns cleaned text
    with page breaks as double newlines."""
    import pdfplumber

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())

    return "\n\n".join(pages_text)


def extract_pdf_with_metadata(pdf_path: str | Path) -> dict:
    """Extract text + metadata from a PDF file.

    Returns dict with text, page_count, metadata, and per-page text.
    """
    import pdfplumber

    pdf_path = Path(pdf_path)
    res = {
        "text": "",
        "page_count": 0,
        "metadata": {},
        "pages": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        res["page_count"] = len(pdf.pages)
        res["metadata"] = pdf.metadata or {}

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            res["pages"].append(
                {
                    "page_number": i + 1,
                    "text": text.strip(),
                    "char_count": len(text.strip()),
                }
            )

    res["text"] = "\n\n".join(p["text"] for p in res["pages"] if p["text"])
    return res
