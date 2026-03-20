"""Supplementary collection to fill gaps in Spanish coverage and HHS content."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Additional seed URLs for gap-filling
SUPPLEMENT_SEEDS: dict[str, dict] = {
    "CDC_ES": {
        "agency": "CDC",
        "domains": ["www.cdc.gov"],
        "seeds": [
            # CDC Spanish topic pages
            "https://www.cdc.gov/spanish/signosvitales/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/seguridad-alimentos/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/saludmental/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/diabetes/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/presionarterial/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/enfermedadescorazon/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/vih/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/embarazo/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/zika/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/tabacoyfumar/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/obesidad/index.html",
            "https://www.cdc.gov/spanish/especialesCDC/lavadodemanos/index.html",
            # Direct Spanish content pages (not landing)
            "https://www.cdc.gov/flu/espanol/index.html",
            "https://www.cdc.gov/flu/espanol/sintomas/index.html",
            "https://www.cdc.gov/flu/espanol/tratamiento/index.html",
            "https://www.cdc.gov/flu/espanol/prevencion/index.html",
            "https://www.cdc.gov/covid/espanol/index.html",
            "https://www.cdc.gov/covid/espanol/sintomas/index.html",
            "https://www.cdc.gov/covid/espanol/prevencion/index.html",
            "https://www.cdc.gov/rsv/espanol/index.html",
            "https://www.cdc.gov/vaccines/espanol/index.html",
        ],
        "path_filters": [r"/spanish/", r"/espanol/"],
        "path_excludes": [r"\.pdf$", r"/mmwr/"],
    },
    "NIH_ES": {
        "agency": "NIH",
        "domains": ["medlineplus.gov"],
        "seeds": [
            "https://medlineplus.gov/spanish/flu.html",
            "https://medlineplus.gov/spanish/covid19.html",
            "https://medlineplus.gov/spanish/foodsafety.html",
            "https://medlineplus.gov/spanish/heartdiseases.html",
            "https://medlineplus.gov/spanish/asthma.html",
            "https://medlineplus.gov/spanish/hivaids.html",
            "https://medlineplus.gov/spanish/obesity.html",
            "https://medlineplus.gov/spanish/anxiety.html",
            "https://medlineplus.gov/spanish/substanceusedisorders.html",
            "https://medlineplus.gov/spanish/hepatitis.html",
            "https://medlineplus.gov/spanish/travelhealth.html",
            "https://medlineplus.gov/spanish/diabetesmedicines.html",
            "https://medlineplus.gov/spanish/highbloodpressure.html",
            "https://medlineplus.gov/spanish/exerciseandphysicalfitness.html",
            "https://medlineplus.gov/spanish/alcoholusedisorderaud.html",
            "https://medlineplus.gov/spanish/opioidusedisorderoud.html",
            "https://medlineplus.gov/spanish/eatingdisorders.html",
            "https://medlineplus.gov/spanish/suicide.html",
            "https://medlineplus.gov/spanish/mentalhealth.html",
            "https://medlineplus.gov/spanish/copingwithdisasters.html",
            "https://medlineplus.gov/spanish/emergencymedicalservices.html",
        ],
        "path_filters": [r"/spanish/"],
        "path_excludes": [r"/ency/", r"/druginfo/", r"\.pdf$"],
    },
    "HHS": {
        "agency": "HHS",
        "domains": ["www.hhs.gov"],
        "seeds": [
            "https://www.hhs.gov/immunization/basics/index.html",
            "https://www.hhs.gov/immunization/get-vaccinated/index.html",
            "https://www.hhs.gov/immunization/vaccines/index.html",
            "https://www.hhs.gov/answers/health-insurance-reform/index.html",
            "https://www.hhs.gov/answers/mental-health-and-substance-abuse/index.html",
            "https://www.hhs.gov/answers/public-health-and-safety/index.html",
            "https://www.hhs.gov/programs/prevention-and-wellness/index.html",
            "https://www.hhs.gov/surgeongeneral/reports-and-publications/index.html",
            "https://www.hhs.gov/opioids/index.html",
        ],
        "path_filters": [
            r"/immunization/",
            r"/answers/",
            r"/programs/",
            r"/opioids/",
            r"/surgeongeneral/",
        ],
        "path_excludes": [
            r"/about/",
            r"/grants/",
            r"/regulations/",
            r"\.pdf$",
            r"/news/",
            r"/blog/",
        ],
    },
    "FDA_ES": {
        "agency": "FDA",
        "domains": ["www.fda.gov"],
        "seeds": [
            "https://www.fda.gov/consumers/articulos-en-espanol",
            "https://www.fda.gov/consumers/free-publications-women/publicaciones-en-espanol",
        ],
        "path_filters": [r"espanol", r"articulos-en-espanol"],
        "path_excludes": [r"\.pdf$"],
    },
}


def run_supplement(output_dir: str | Path = "data/raw", max_pages: int = 40):
    """Run supplementary collection to fill coverage gaps."""
    from .source_collector import collect_agency

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest to avoid re-collecting
    manifest_path = output_dir / "_manifest.json"
    existing_urls: set[str] = set()
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        existing_urls = {d["url"] for d in existing}

    all_new: list[dict] = []

    for key, config in SUPPLEMENT_SEEDS.items():
        agency = config["agency"]
        crawl_config = {
            "domains": config["domains"],
            "seeds": [u for u in config["seeds"] if u not in existing_urls],
            "path_filters": config.get("path_filters", []),
            "path_excludes": config.get("path_excludes", []),
        }
        if not crawl_config["seeds"]:
            logger.info("[%s] All seeds already collected, skipping", key)
            continue

        logger.info("[%s] Collecting up to %d supplementary pages", key, max_pages)
        docs = collect_agency(
            agency, crawl_config, output_dir, max_pages=max_pages, max_crawl_depth=2
        )

        for d in docs:
            if d.url not in existing_urls:
                all_new.append(d.to_metadata())
                existing_urls.add(d.url)

    # Append to manifest
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = []
    manifest.extend(all_new)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("Supplementary collection: %d new documents", len(all_new))
    return all_new


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    run_supplement(max_pages=40)
