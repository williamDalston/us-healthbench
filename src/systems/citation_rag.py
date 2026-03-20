"""Baseline C: RAG with citation-constrained answering."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone

from .rag import build_rag_context, retrieve_chunks

logger = logging.getLogger(__name__)

CITATION_RAG_SYSTEM_PROMPT = (
    "You are a health information assistant with access to official U.S. "
    "public-health guidance.\n"
    "Answer the user's question based ONLY on the provided source documents.\n\n"
    "CRITICAL RULES:\n"
    "1. Every factual claim in your answer MUST be followed by a citation in the format "
    "[Source X — chunk_id].\n"
    "2. If you cannot support a claim from the provided sources, do NOT include it in your "
    "answer.\n"
    "3. If the sources do not contain enough information to answer the question, explicitly state "
    "what you cannot answer and why.\n"
    "4. Recommend consulting a healthcare provider when appropriate.\n"
    "5. Do not add information beyond what the sources explicitly state.\n"
    "6. Use plain, consumer-friendly language.\n\n"
    "Example citation format:\n"
    '"You should stay home while you have a fever [Source 1 — cdc_flu_2026_014_c03]."\n'
)


def answer_with_citation_rag(
    question,
    collection,
    llm_client,
    model="gpt-4o",
    language="en",
    n_retrieve=5,
):
    """Answer using RAG with mandatory citation of source chunks.

    The model is told to cite specific chunk IDs for every claim.
    """
    lang_instruction = ""
    if language == "es":
        lang_instruction = (
            "\n\nResponde en español. Cada afirmación debe incluir una cita "
            "en el formato [Source X — chunk_id]."
        )

    start = time.time()
    chunks = retrieve_chunks(question, collection, n_results=n_retrieve, language=language)
    ctx = build_rag_context(chunks)

    user_message = f"""Based on the following official U.S. public-health guidance sources,
answer this question.
EVERY factual claim must cite its source using [Source X — chunk_id] format.

QUESTION: {question}

SOURCE DOCUMENTS:
{ctx}"""

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CITATION_RAG_SYSTEM_PROMPT + lang_instruction},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=2000,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    answer = response.choices[0].message.content
    usage = response.usage

    # pull cited chunk IDs out of the answer text
    cited_ids = re.findall(r"\[Source \d+ — (\S+?)\]", answer)
    cited_ids = list(dict.fromkeys(cited_ids))  # dedupe, keep order

    return {
        "system": "citation_rag",
        "model_name": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": answer,
        "cited_chunks": cited_ids,
        "cited_urls": [],
        "retrieval_context": chunks,
        "agent_trace": None,
        "latency_ms": elapsed_ms,
        "token_counts": {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
        },
    }


def run_baseline_c(
    items: list[dict],
    collection,
    llm_client,
    model: str = "gpt-4o",
    output_path=None,
) -> list[dict]:
    """Run Baseline C (citation-constrained RAG) on all benchmark items."""
    outputs = []

    for item in items:
        item_id = item["item_id"]
        q = item["question"]
        lang = item.get("language", "en")

        logger.info("Baseline C -- item %s", item_id)
        output = answer_with_citation_rag(q, collection, llm_client, model, lang)
        output["item_id"] = item_id
        output["output_id"] = (
            f"out_citation_rag_{item_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        )
        outputs.append(output)

    if output_path:
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for out in outputs:
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

    return outputs
