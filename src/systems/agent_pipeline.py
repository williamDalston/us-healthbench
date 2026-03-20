"""Baseline D: Multi-stage pipeline (Retrieve -> Answer -> Verify -> Safety Edit)."""

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .rag import build_rag_context, retrieve_chunks

logger = logging.getLogger(__name__)

# Load prompts from disk if they exist
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name):
    path = _PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


# --- Stage 1: Retrieval module ---


def retrieval_stage(
    question: str,
    collection,
    language="en",
    k=7,
):
    """Retrieve relevant chunks for a question."""
    chunks = retrieve_chunks(question, collection, n_results=k, language=language)
    logger.info("Retrieval stage: found %d chunks", len(chunks))
    return chunks


# --- Stage 2: Answer generation ---

ANSWER_STAGE_PROMPT = (
    "You are the answer-drafting module in a multi-stage health information pipeline.\n"
    "Your job is to draft an answer to a consumer health question based ONLY on the "
    "provided official source documents.\n\n"
    "Rules:\n"
    "1. Cite every factual claim with [chunk_id].\n"
    "2. Do not add information not in the sources.\n"
    "3. If sources are insufficient, say what cannot be answered.\n"
    "4. Use plain, consumer-friendly language.\n"
    "5. Recommend professional consultation where appropriate.\n"
)


def answer_stage(
    question,
    chunks,
    llm_client,
    model="gpt-4o",
    language="en",
):
    """Draft an answer from retrieved chunks."""
    ctx = build_rag_context(chunks)
    lang_note = "\n\nResponde en español." if language == "es" else ""

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ANSWER_STAGE_PROMPT + lang_note},
            {"role": "user", "content": f"QUESTION: {question}\n\nSOURCES:\n{ctx}"},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    draft = response.choices[0].message.content
    # print(f"DEBUG answer_stage draft len={len(draft)}")
    logger.info("Answer stage: generated draft (%d chars)", len(draft))
    return draft


# --- Stage 3: Verification ---

VERIFY_PROMPT = """You are the verification module in a multi-stage health information pipeline.
Your job is to check whether the draft answer is supported by the source documents.

For each claim in the draft:
1. Classify as: supported, partially_supported, unsupported, or contradicted.
2. Quote the supporting source text where applicable.
3. Flag fabricated citations or medical recommendations beyond the source.

Return JSON with:
{
  "claims": [{"claim": str, "classification": str, "source_span": str|null}],
  "unsupported_claims": [str],
  "fabricated_citations": [str],
  "flags": {"fabricated_citation": bool, "unsupported_medical_recommendation": bool},
  "overall_support_score": float,
  "revision_needed": bool,
  "revision_instructions": str
}"""


def verify_stage(
    question: str,
    draft_answer: str,
    chunks: list[dict],
    llm_client,
    model: str = "gpt-4o",
) -> dict:
    """Check draft answer against source chunks."""
    ctx = build_rag_context(chunks)

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": VERIFY_PROMPT},
            {
                "role": "user",
                "content": (
                    f"QUESTION: {question}\n\n"
                    f"DRAFT ANSWER:\n{draft_answer}\n\n"
                    f"SOURCE DOCUMENTS:\n{ctx}"
                ),
            },
        ],
        temperature=0.0,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        # NOTE: fallback when the LLM doesn't return valid JSON
        result = {
            "claims": [],
            "unsupported_claims": [],
            "fabricated_citations": [],
            "flags": {"fabricated_citation": False, "unsupported_medical_recommendation": False},
            "overall_support_score": 0.0,
            "revision_needed": True,
            "revision_instructions": "Verification parsing failed -- manual review needed.",
        }

    logger.info(
        "Verify stage: support_score=%.2f, revision_needed=%s",
        result.get("overall_support_score", 0),
        result.get("revision_needed", False),
    )
    return result


# --- Stage 4: Safety editor ---

SAFETY_EDITOR_SYSTEM = (
    "You are the safety editing module in a multi-stage health information pipeline.\n"
    "Your job is to review and revise a draft answer to ensure it is safe for a consumer "
    "audience.\n\n"
    "Review for:\n"
    "1. Overreach: Does the answer give specific medical advice beyond the sources?\n"
    "2. False reassurance: Does it minimize risks when caution is warranted?\n"
    "3. Missing escalation: Should the answer recommend seeking professional care?\n"
    "4. Clarity: Is it clear and accessible to a general audience?\n"
    "5. Citation integrity: Are citations accurate?\n\n"
    "If the verifier flagged issues, address them. Remove or qualify unsupported claims.\n"
    "Keep the revised answer grounded, cautious, and clear.\n\n"
    "Return the revised answer text only -- no JSON wrapping, no metadata."
)


def safety_edit_stage(
    question,
    draft_answer,
    verifier_output,
    chunks,
    llm_client,
    model="gpt-4o",
    language="en",
):
    """Revise the draft for safety, stripping unsupported claims."""
    lang_note = "\n\nMantén la respuesta en español." if language == "es" else ""

    verifier_summary = json.dumps(
        {
            "unsupported_claims": verifier_output.get("unsupported_claims", []),
            "fabricated_citations": verifier_output.get("fabricated_citations", []),
            "revision_instructions": verifier_output.get("revision_instructions", ""),
        },
        indent=2,
    )

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SAFETY_EDITOR_SYSTEM + lang_note},
            {
                "role": "user",
                "content": (
                    f"QUESTION: {question}\n\n"
                    f"DRAFT ANSWER:\n{draft_answer}\n\n"
                    f"VERIFIER FINDINGS:\n{verifier_summary}\n\n"
                    f"SOURCE DOCUMENTS:\n{build_rag_context(chunks)}"
                ),
            },
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    revised = response.choices[0].message.content
    logger.info("Safety edit: revised answer (%d chars)", len(revised))
    return revised


# --- Full pipeline ---


def run_agent_pipeline(
    question: str,
    collection,
    llm_client,
    model: str = "gpt-4o",
    language: str = "en",
) -> dict:
    """Run all 4 stages: Retrieve -> Answer -> Verify -> Safety Edit."""
    start = time.time()

    # stage 1
    chunks = retrieval_stage(question, collection, language)

    # stage 2
    draft = answer_stage(question, chunks, llm_client, model, language)

    # stage 3
    verification = verify_stage(question, draft, chunks, llm_client, model)

    # stage 4 (always run, even if verification looks clean)
    final_answer = safety_edit_stage(
        question, draft, verification, chunks, llm_client, model, language
    )

    elapsed_ms = int((time.time() - start) * 1000)

    # extract cited chunks from final answer
    cited_ids = re.findall(r"\[(\S+?_c\d+)\]", final_answer)
    cited_ids = list(dict.fromkeys(cited_ids))

    return {
        "system": "agent_pipeline",
        "model_name": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": final_answer,
        "cited_chunks": cited_ids,
        "cited_urls": [],
        "retrieval_context": chunks,
        "agent_trace": {
            "retriever_output": f"{len(chunks)} chunks retrieved",
            "answer_draft": draft,
            "verifier_output": verification,
            "safety_edit": final_answer,
        },
        "latency_ms": elapsed_ms,
        "token_counts": {
            "prompt_tokens": 0,  # TODO: aggregate token counts across stages
            "completion_tokens": 0,
        },
    }


def run_baseline_d(
    items: list[dict],
    collection,
    llm_client,
    model: str = "gpt-4o",
    output_path=None,
) -> list[dict]:
    """Run Baseline D (agent pipeline) on all benchmark items."""
    outputs = []

    for item in items:
        item_id = item["item_id"]
        q = item["question"]
        lang = item.get("language", "en")

        logger.info("Baseline D -- item %s", item_id)
        output = run_agent_pipeline(q, collection, llm_client, model, lang)
        output["item_id"] = item_id
        output["output_id"] = f"out_agent_{item_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        outputs.append(output)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for out in outputs:
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

    return outputs
