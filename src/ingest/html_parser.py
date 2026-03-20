"""Parse HTML from agency pages into clean text with structure preservation.

Uses trafilatura as the primary extractor with a BeautifulSoup fallback.
"""

import logging
import re

import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_html_to_text(html: str, preserve_headings: bool = True) -> str:
    """Convert HTML to clean text suitable for chunking.

    Tries trafilatura first, falls back to bs4 if the result is too short.
    """
    if not html or len(html) < 100:
        return ""

    # try trafilatura first
    text = _extract_with_trafilatura(html, preserve_headings)
    if text and len(text) >= 200:
        return text

    # NOTE: bs4 fallback is slower but more reliable for gov sites with weird markup
    text = _extract_with_bs4(html, preserve_headings)
    return text


def _extract_with_trafilatura(html, preserve_headings):
    # primary extraction via trafilatura
    try:
        res = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_links=False,
            include_images=False,
            favor_precision=False,
            favor_recall=True,
            output_format="txt",
        )
        if not res:
            return ""

        if preserve_headings:
            # trafilatura loses heading levels. Re-extract headings from HTML
            # and try to insert markers where they appear in the text.
            res = _reinsert_heading_markers(html, res)

        # Clean up
        res = re.sub(r"\n{3,}", "\n\n", res)
        res = res.strip()
        return res

    except Exception as e:
        logger.debug("trafilatura extraction failed: %s", e)
        return ""


def _extract_with_bs4(html, preserve_headings):
    # fallback extraction using beautifulsoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag_name in ["script", "style", "nav", "footer", "aside", "form", "noscript"]:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove specific non-content classes/roles (but NOT .syndicate -- that's CDC content!)
    for selector in [
        '[role="navigation"]',
        '[role="banner"]',
        '[role="contentinfo"]',
        ".breadcrumb",
        ".share-tools",
        ".social-media",
    ]:
        for el in soup.select(selector):
            el.decompose()

    # Find main content area
    main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.body or soup

    if not main:
        return ""

    parts: list[str] = []

    for element in main.descendants:
        if not hasattr(element, "name"):
            # NavigableString
            text = str(element).strip()
            if (
                text
                and element.parent
                and element.parent.name
                not in (
                    "script",
                    "style",
                    "nav",
                    "footer",
                )
            ):
                parts.append(text)
        elif element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            heading_text = element.get_text(strip=True)
            if heading_text and preserve_headings:
                parts.append(f"\n\n[{element.name}] {heading_text}\n")
        elif element.name == "br":
            parts.append("\n")
        elif element.name in ("p", "div", "section", "li"):
            # Add paragraph break before block elements
            if parts and not parts[-1].endswith("\n"):
                parts.append("\n")

    text = " ".join(parts)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n +", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _reinsert_heading_markers(html: str, text: str) -> str:
    """Extract headings from HTML and insert [hN] markers into the plain text."""
    soup = BeautifulSoup(html, "html.parser")
    headings: list[tuple[str, str]] = []  # (level, text)

    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            h_text = h.get_text(strip=True)
            if h_text and len(h_text) > 2:
                headings.append((f"h{level}", h_text))

    # Insert markers: find each heading text in the output and prefix it
    for level, h_text in headings:
        marker = f"[{level}] {h_text}"
        if marker in text:
            continue
        # Try exact match replacement (first occurrence only)
        escaped = re.escape(h_text)
        pattern = rf"(?m)^{escaped}$"
        replacement = f"[{level}] {h_text}"
        text_new = re.sub(pattern, replacement, text, count=1)
        if text_new == text:
            # Try a looser match: heading text at start of line
            pattern = rf"\n{escaped}\n"
            text_new = re.sub(pattern, f"\n{replacement}\n", text, count=1)
        text = text_new

    return text


def extract_structured_sections(html: str) -> list[dict]:
    """Extract structured sections from HTML as a list of
    {section_title, level, text} dicts."""
    full_text = clean_html_to_text(html, preserve_headings=True)
    if not full_text:
        return []

    sections: list[dict] = []
    current_title = "Introduction"
    current_level = 0
    current_lines: list[str] = []

    for line in full_text.split("\n"):
        heading_match = re.match(r"^\[h(\d)\]\s+(.+)$", line.strip())
        if heading_match:
            if current_lines:
                text = "\n".join(current_lines).strip()
                if text:
                    sections.append(
                        {
                            "section_title": current_title,
                            "level": current_level,
                            "text": text,
                        }
                    )
                current_lines = []
            current_level = int(heading_match.group(1))
            current_title = heading_match.group(2).strip()
        else:
            if line.strip():
                current_lines.append(line.strip())

    if current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(
                {
                    "section_title": current_title,
                    "level": current_level,
                    "text": text,
                }
            )

    return sections


def extract_faq_pairs(html: str) -> list[dict]:
    """Extract FAQ question-answer pairs from common HTML patterns
    (accordion, dl/dt/dd, etc.)."""
    soup = BeautifulSoup(html, "html.parser")
    pairs: list[dict] = []

    # Pattern 1: Definition lists (dt/dd)
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            question = dt.get_text(strip=True)
            answer = dd.get_text(strip=True)
            if question and answer:
                pairs.append({"question": question, "answer": answer})

    # Pattern 2: Accordion patterns (common on CDC pages)
    for accordion in soup.find_all(class_=re.compile(r"accordion|collapse|faq", re.I)):
        header = accordion.find(class_=re.compile(r"header|title|question", re.I))
        body = accordion.find(class_=re.compile(r"body|content|answer", re.I))
        if header and body:
            question = header.get_text(strip=True)
            answer = body.get_text(strip=True)
            if question and answer:
                pairs.append({"question": question, "answer": answer})

    return pairs
