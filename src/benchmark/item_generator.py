"""Generate benchmark items from chunked source documents via the item generation pipeline."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the item writer prompt template
ITEM_WRITER_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "item_writer.md"


def load_prompt_template():
    # loads the prompt template used by the generation module
    return ITEM_WRITER_PROMPT_PATH.read_text(encoding="utf-8")


def build_item_generation_prompt(
    doc_id: str,
    chunk_id: str,
    chunk_text: str,
    agency: str,
    topic: str,
    language: str,
) -> str:
    """Build a complete prompt for the item generation pipeline."""
    tmpl = load_prompt_template()
    context = f"""
## Source Context

- doc_id: {doc_id}
- chunk_id: {chunk_id}
- agency: {agency}
- topic: {topic}
- language: {language}

## Source Text

{chunk_text}
"""
    return tmpl + "\n\n---\n" + context


def generate_items_for_chunk(
    doc_id: str,
    chunk: dict,
    agency: str,
    topic: str,
    language: str,
    llm_client,
    model: str = "gpt-4o",
    items_per_chunk: int = 1,
) -> list[dict]:
    """Generate benchmark items for a single chunk using the LLM.

    Calls the model once per requested item. Returned dicts follow
    the benchmark item schema.
    """
    prompt = build_item_generation_prompt(
        doc_id=doc_id,
        chunk_id=chunk["chunk_id"],
        chunk_text=chunk["text"],
        agency=agency,
        topic=topic,
        language=language,
    )

    items: list[dict] = []
    for _ in range(items_per_chunk):
        try:
            resp = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are generating benchmark items for US-HealthBench. "
                            "Return valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            item = json.loads(content)

            # Ensure source_documents reference is correct
            if "source_documents" not in item:
                item["source_documents"] = [
                    {
                        "doc_id": doc_id,
                        "chunks": [chunk["chunk_id"]],
                    }
                ]

            items.append(item)
            logger.info("Generated item for chunk %s", chunk["chunk_id"])

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning("Failed to generate item for %s: %s", chunk["chunk_id"], e)

    return items


# NOTE: this iterates sequentially; batching would speed things up
def generate_items_for_document(
    doc: dict,
    chunks: list[dict],
    llm_client,
    model: str = "gpt-4o",
    items_per_chunk: int = 1,
) -> list[dict]:
    """Generate benchmark items for every chunk in a document."""
    all_items: list[dict] = []

    for chunk in chunks:
        items = generate_items_for_chunk(
            doc_id=doc["doc_id"],
            chunk=chunk,
            agency=doc["agency"],
            topic=doc["topic"],
            language=doc["language"],
            llm_client=llm_client,
            model=model,
            items_per_chunk=items_per_chunk,
        )
        all_items.extend(items)

    logger.info(
        "Generated %d items for document %s (%d chunks)",
        len(all_items),
        doc["doc_id"],
        len(chunks),
    )
    return all_items


def assign_item_ids(items, start_seq=1):
    """Assign sequential item_ids to a list of benchmark items."""
    for i, item in enumerate(items):
        item["item_id"] = f"ushb_{start_seq + i:06d}"
    return items


def save_items(items: list[dict], output_path: str | Path) -> None:
    """Save benchmark items as JSONL."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # print(f"Writing {len(items)} items to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info("Saved %d items to %s", len(items), output_path)


def load_items(input_path: str | Path) -> list[dict]:
    """Load benchmark items from JSONL."""
    items: list[dict] = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items
