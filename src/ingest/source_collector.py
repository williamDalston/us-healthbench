"""Collect source documents from official U.S. public-health agency websites.

Crawls seed URLs, follows internal links to consumer-facing pages,
and saves raw HTML with metadata. Respects rate limits and robots.txt etiquette.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Agency seed URLs -- curated consumer-facing entry points
AGENCY_SEEDS: dict[str, dict] = {
    "CDC": {
        "domains": ["www.cdc.gov"],
        "seeds": [
            # English -- topic landing pages
            "https://www.cdc.gov/flu/index.html",
            "https://www.cdc.gov/flu/treatment/index.html",
            "https://www.cdc.gov/flu/symptoms/index.html",
            "https://www.cdc.gov/flu/prevent/index.html",
            "https://www.cdc.gov/covid/index.html",
            "https://www.cdc.gov/covid/prevention/index.html",
            "https://www.cdc.gov/covid/symptoms/index.html",
            "https://www.cdc.gov/covid/treatment/index.html",
            "https://www.cdc.gov/rsv/index.html",
            "https://www.cdc.gov/rsv/about/symptoms.html",
            "https://www.cdc.gov/vaccines/index.html",
            "https://www.cdc.gov/vaccines/parents/index.html",
            "https://www.cdc.gov/vaccines/schedules/index.html",
            "https://www.cdc.gov/food-safety/index.html",
            "https://www.cdc.gov/food-safety/prevention/index.html",
            "https://www.cdc.gov/maternal-health/index.html",
            "https://www.cdc.gov/mental-health/index.html",
            "https://www.cdc.gov/suicide/index.html",
            "https://www.cdc.gov/tobacco/index.html",
            "https://www.cdc.gov/diabetes/index.html",
            "https://www.cdc.gov/heart-disease/index.html",
            "https://www.cdc.gov/cancer/index.html",
            "https://www.cdc.gov/hiv/index.html",
            "https://www.cdc.gov/std/default.htm",
            "https://www.cdc.gov/hepatitis/index.html",
            "https://www.cdc.gov/travel/index.html",
            "https://www.cdc.gov/emergency-preparedness/index.html",
            "https://www.cdc.gov/handwashing/index.html",
            "https://www.cdc.gov/nutrition/index.html",
            "https://www.cdc.gov/physical-activity/index.html",
            "https://www.cdc.gov/sleep/index.html",
            # Spanish
            "https://www.cdc.gov/spanish/gripe/index.html",
            "https://www.cdc.gov/spanish/covid/index.html",
            "https://www.cdc.gov/spanish/vacunas/index.html",
            "https://www.cdc.gov/spanish/cancer/index.html",
            "https://www.cdc.gov/spanish/diabetes/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/seguridad-alimentos/index.html",
        ],
        "path_filters": [
            # Stay on consumer-facing pages
            r"/flu/",
            r"/covid/",
            r"/rsv/",
            r"/vaccines/",
            r"/food-safety/",
            r"/maternal-health/",
            r"/mental-health/",
            r"/suicide/",
            r"/tobacco/",
            r"/diabetes/",
            r"/heart-disease/",
            r"/cancer/",
            r"/hiv/",
            r"/std/",
            r"/hepatitis/",
            r"/travel/",
            r"/emergency-preparedness/",
            r"/handwashing/",
            r"/nutrition/",
            r"/physical-activity/",
            r"/sleep/",
            r"/spanish/",
        ],
        "path_excludes": [
            r"/mmwr/",
            r"/eid/",
            r"/media/",
            r"/about/",
            r"/contact/",
            r"/jobs/",
            r"/grants/",
            r"/data-research/",
            r"/surveillance/",
            r"\.pdf$",
            r"\.zip$",
        ],
    },
    "NIH": {
        "domains": ["www.nih.gov", "medlineplus.gov"],
        "seeds": [
            "https://medlineplus.gov/flu.html",
            "https://medlineplus.gov/commoncold.html",
            "https://medlineplus.gov/covid19.html",
            "https://medlineplus.gov/immunization.html",
            "https://medlineplus.gov/foodsafety.html",
            "https://medlineplus.gov/prenatalcare.html",
            "https://medlineplus.gov/depression.html",
            "https://medlineplus.gov/anxiety.html",
            "https://medlineplus.gov/substanceusedisorders.html",
            "https://medlineplus.gov/diabetes.html",
            "https://medlineplus.gov/heartdiseases.html",
            "https://medlineplus.gov/cancer.html",
            "https://medlineplus.gov/highbloodpressure.html",
            "https://medlineplus.gov/asthma.html",
            "https://medlineplus.gov/hivaids.html",
            "https://medlineplus.gov/hepatitis.html",
            "https://medlineplus.gov/travelhealth.html",
            "https://medlineplus.gov/emergencymedicalservices.html",
            "https://medlineplus.gov/obesity.html",
            "https://medlineplus.gov/druguse.html",
            "https://medlineplus.gov/alcoholusedisorderaud.html",
            "https://medlineplus.gov/opioidusedisorderoud.html",
            # Spanish
            "https://medlineplus.gov/spanish/flu.html",
            "https://medlineplus.gov/spanish/covid19.html",
            "https://medlineplus.gov/spanish/immunization.html",
            "https://medlineplus.gov/spanish/diabetes.html",
            "https://medlineplus.gov/spanish/cancer.html",
            "https://medlineplus.gov/spanish/depression.html",
            "https://medlineplus.gov/spanish/prenatalcare.html",
            "https://medlineplus.gov/spanish/highbloodpressure.html",
        ],
        "path_filters": [],  # medlineplus pages are already consumer-facing
        "path_excludes": [
            r"/ency/",
            r"/druginfo/",
            r"\.pdf$",
            r"/about/",
        ],
    },
    "FDA": {
        "domains": ["www.fda.gov"],
        "seeds": [
            "https://www.fda.gov/consumers/consumer-updates",
            "https://www.fda.gov/consumers/free-publications-women",
            "https://www.fda.gov/consumers/minority-health-and-health-equity/multicultural-resources-consumers",
            "https://www.fda.gov/drugs/safe-use-medicines",
            "https://www.fda.gov/vaccines-blood-biologics/vaccines",
            "https://www.fda.gov/food/food-safety-during-emergencies",
            "https://www.fda.gov/food/buy-store-serve-safe-food",
            "https://www.fda.gov/tobacco-products/health-effects-tobacco-use",
            "https://www.fda.gov/consumers/articulos-en-espanol",
        ],
        "path_filters": [
            r"/consumers/",
            r"/drugs/safe-use",
            r"/food/",
            r"/vaccines-blood-biologics/vaccines",
            r"/tobacco-products/health-effects",
        ],
        "path_excludes": [
            r"/regulatory-information/",
            r"/inspections/",
            r"\.pdf$",
            r"/about-fda/",
            r"/news-events/",
        ],
    },
    "HHS": {
        "domains": ["www.hhs.gov"],
        "seeds": [
            "https://www.hhs.gov/programs/topic-sites/index.html",
            "https://www.hhs.gov/immunization/index.html",
            "https://www.hhs.gov/answers/index.html",
            "https://www.hhs.gov/programs/prevention-and-wellness/index.html",
        ],
        "path_filters": [
            r"/programs/",
            r"/immunization/",
            r"/answers/",
        ],
        "path_excludes": [
            r"/about/",
            r"/grants/",
            r"/regulations/",
            r"\.pdf$",
        ],
    },
    "CMS": {
        "domains": ["www.cms.gov", "www.medicare.gov", "www.medicaid.gov"],
        "seeds": [
            "https://www.medicare.gov/what-medicare-covers",
            "https://www.medicare.gov/basics/get-started-with-medicare",
            "https://www.medicare.gov/drug-coverage-part-d",
            "https://www.medicare.gov/health-drug-plans",
            "https://www.medicaid.gov/about-us/beneficiary-resources/index.html",
        ],
        "path_filters": [],
        "path_excludes": [
            r"/regulations/",
            r"/newsroom/",
            r"\.pdf$",
        ],
    },
}

HEADERS = {
    "User-Agent": (
        "US-HealthBench-Research-Bot/0.1 "
        "(Academic research benchmark for public health AI evaluation; "
        "contact: ushealthbench@example.com)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.5  # seconds between requests to same domain
MIN_CONTENT_LENGTH = 500  # minimum chars for a page to be useful


@dataclass
class SourceDocument:
    """A collected source document with metadata."""

    doc_id: str
    agency: str
    url: str
    title: str
    language: str
    topic: str
    content_type: str
    intended_audience: str
    last_updated: str | None
    date_collected: str
    public_domain_status: str
    raw_html: str | None = None
    raw_text: str | None = None
    chunks: list[dict] = field(default_factory=list)

    def to_metadata(self) -> dict:
        """Return JSON-serializable metadata (no raw content)."""
        return {
            "doc_id": self.doc_id,
            "agency": self.agency,
            "url": self.url,
            "title": self.title,
            "language": self.language,
            "topic": self.topic,
            "content_type": self.content_type,
            "intended_audience": self.intended_audience,
            "last_updated": self.last_updated,
            "date_collected": self.date_collected,
            "public_domain_status": self.public_domain_status,
        }


# Helpers


def detect_language(url, text):
    """Detect language from URL patterns and content."""
    spanish_url = ["/spanish/", "/espanol/", "/es/", "/spanish.", "articulos-en-espanol"]
    if any(ind in url.lower() for ind in spanish_url):
        return "es"
    try:
        from langdetect import detect

        detected = detect(text[:3000])
        return "es" if detected == "es" else "en"
    except Exception:
        return "en"


def infer_topic(url: str, title: str) -> str:
    """Infer topic area from URL and title keywords."""
    text = f"{url} {title}".lower()
    mapping = {
        "vaccination": ["vaccine", "vaccination", "immuniz", "vacuna", "inmuniz"],
        "respiratory_illness": [
            "flu",
            "influenza",
            "covid",
            "rsv",
            "respiratory",
            "gripe",
            "cold",
            "pneumonia",
            "bronchitis",
        ],
        "food_safety": ["food safety", "foodborne", "food poisoning", "seguridad alimentaria"],
        "pregnancy_maternal": ["pregnan", "maternal", "prenatal", "embaraz", "breastfeed"],
        "mental_health_substance": [
            "mental health",
            "depression",
            "anxiety",
            "suicide",
            "substance",
            "opioid",
            "alcohol",
            "drug use",
            "salud mental",
            "adicci",
        ],
        "insurance_access": ["medicare", "medicaid", "insurance", "coverage", "seguro médico"],
        "chronic_disease": [
            "diabetes",
            "heart disease",
            "cancer",
            "hypertension",
            "blood pressure",
            "asthma",
            "obesity",
            "chronic",
            "crónic",
        ],
        "travel_health": ["travel health", "travelers", "viaj"],
        "infectious_disease": [
            "hiv",
            "aids",
            "hepatitis",
            "std",
            "sti",
            "sexually transmitted",
            "tuberculosis",
            "malaria",
            "infectious",
        ],
        "emergency_preparedness": [
            "emergency",
            "preparedness",
            "disaster",
            "emergencia",
        ],
    }
    for topic, keywords in mapping.items():
        if any(kw in text for kw in keywords):
            return topic
    return "general"


def generate_doc_id(agency, topic, seq):
    year = date.today().year
    topic_short = topic.split("_")[0][:8]
    return f"{agency.lower()}_{topic_short}_{year}_{seq:03d}"


def extract_metadata(html: str, url: str) -> dict:
    """Extract page title, last-updated date from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    # Fallback: h1
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    last_updated = None
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        if name in (
            "date",
            "dcterms.modified",
            "last-modified",
            "article:modified_time",
            "dc.date.modified",
        ):
            last_updated = meta.get("content", "")
            break

    # CDC-specific: look for "Page last reviewed" text
    if not last_updated:
        reviewed = soup.find(string=re.compile(r"(last reviewed|last updated|page last)", re.I))
        if reviewed:
            date_match = re.search(r"(\w+ \d{1,2}, \d{4})", str(reviewed))
            if date_match:
                last_updated = date_match.group(1)

    return {"title": title, "last_updated": last_updated}


def get_text_length(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return len(soup.get_text(strip=True))


def extract_links(html: str, base_url: str, allowed_domains: list[str]) -> list[str]:
    """Extract internal links from HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # Skip anchors, mailto, tel, javascript
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        # Only keep links on allowed domains
        if parsed.hostname and parsed.hostname in allowed_domains:
            # Normalize: remove fragment, ensure https
            clean = f"https://{parsed.hostname}{parsed.path}"
            if parsed.query:
                clean += f"?{parsed.query}"
            links.append(clean)

    return links


def should_crawl(url, path_filters, path_excludes):
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Check excludes first
    for pattern in path_excludes:
        if re.search(pattern, path):
            return False

    # If no path_filters, accept everything not excluded
    if not path_filters:
        return True

    return any(re.search(pattern, path) for pattern in path_filters)


# --- Main collector ---


def fetch_page(url: str) -> tuple[str, int]:
    """Fetch a single page. Sleeps for rate limiting."""
    time.sleep(RATE_LIMIT_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "html" not in ct.lower():
            return "", 0
        return resp.text, resp.status_code
    except requests.RequestException as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return "", 0


def collect_agency(
    agency: str,
    config: dict,
    output_dir: Path,
    max_pages: int = 100,
    max_crawl_depth: int = 2,
) -> list[SourceDocument]:
    """BFS crawl of one agency's consumer-facing pages."""
    seeds = config["seeds"]
    domains = config["domains"]
    path_filters = config.get("path_filters", [])
    path_excludes = config.get("path_excludes", [])

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()  # (url, depth)
    collected: list[SourceDocument] = []
    seq_counter: dict[str, int] = {}

    for url in seeds:
        if url not in visited:
            queue.append((url, 0))
            visited.add(url)

    while queue and len(collected) < max_pages:
        url, depth = queue.popleft()

        html, status = fetch_page(url)
        if status != 200 or not html:
            continue

        # Check content length
        n = get_text_length(html)
        if n < MIN_CONTENT_LENGTH:
            logger.debug("Skipping %s — too short (%d chars)", url, n)
            continue

        meta = extract_metadata(html, url)
        if not meta["title"]:
            logger.debug("Skipping %s — no title", url)
            continue

        language = detect_language(url, html)
        topic = infer_topic(url, meta["title"])

        # Generate doc_id
        key = f"{agency}_{topic}"
        seq_counter[key] = seq_counter.get(key, 0) + 1
        doc_id = generate_doc_id(agency, topic, seq_counter[key])

        doc = SourceDocument(
            doc_id=doc_id,
            agency=agency,
            url=url,
            title=meta["title"],
            language=language,
            topic=topic,
            content_type="webpage",
            intended_audience="consumer",
            last_updated=meta["last_updated"],
            date_collected=date.today().isoformat(),
            public_domain_status="likely_us_federal_work",
            raw_html=html,
        )
        collected.append(doc)
        # print(f"  collected {doc_id}: {meta['title'][:50]}")

        # Save files
        (output_dir / f"{doc_id}.html").write_text(html, encoding="utf-8")
        (output_dir / f"{doc_id}.json").write_text(
            json.dumps(doc.to_metadata(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(
            "[%s] %3d  %-45s  [%s] %s",
            agency,
            len(collected),
            doc_id,
            language,
            meta["title"][:60],
        )

        # TODO: handle rate limit retries more gracefully (exp backoff?)
        # Discover new links (BFS, depth-limited)
        if depth < max_crawl_depth:
            child_links = extract_links(html, url, domains)
            for link in child_links:
                if link not in visited and should_crawl(link, path_filters, path_excludes):
                    visited.add(link)
                    queue.append((link, depth + 1))

    logger.info("[%s] Collected %d pages", agency, len(collected))
    return collected


def collect_sources(
    output_dir: str | Path,
    agencies: list[str] | None = None,
    max_pages_per_agency: int = 100,
    max_crawl_depth: int = 2,
) -> list[SourceDocument]:
    """Collect source documents from all configured agencies.

    Returns list of all collected SourceDocument objects.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agencies = agencies or list(AGENCY_SEEDS.keys())
    all_docs: list[SourceDocument] = []

    for agency in agencies:
        if agency not in AGENCY_SEEDS:
            logger.warning("Unknown agency: %s — skipping", agency)
            continue
        config = AGENCY_SEEDS[agency]
        docs = collect_agency(agency, config, output_dir, max_pages_per_agency, max_crawl_depth)
        all_docs.extend(docs)

    # Save manifest
    manifest = [d.to_metadata() for d in all_docs]
    manifest_path = output_dir / "_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Total collected: %d documents. Manifest: %s", len(all_docs), manifest_path)
    return all_docs


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    # Day 2: collect up to 80 pages per agency (400 target total)
    docs = collect_sources("data/raw", max_pages_per_agency=80, max_crawl_depth=2)
    print(f"\nCollection complete: {len(docs)} documents.")
