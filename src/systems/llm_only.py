"""Baseline A: Plain LLM answering without retrieval."""

import json
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful health information assistant. Answer the user's health question clearly, "
    "accurately, and in plain language.\n"
    "If you are unsure about something, say so.\n"
    "If the question requires professional medical advice, recommend consulting a healthcare "
    "provider.\n\n"
    "Important guidelines:\n"
    "- Use only information you are confident about\n"
    "- Do not make up statistics or cite sources you are unsure of\n"
    "- Recommend seeking professional medical care when appropriate\n"
    "- Be clear about what you know and what you are uncertain about\n"
)


def answer_question(
    question: str,
    llm_client,
    model: str = "gpt-4o",
    language: str = "en",
) -> dict:
    """Call the LLM with no retrieval context, just the question."""
    lang_instruction = ""
    if language == "es":
        lang_instruction = "\n\nResponde en español."

    # TODO: swap in real LLM client when API keys available
    start = time.time()
    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + lang_instruction},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    answer = response.choices[0].message.content
    usage = response.usage
    # print(f"DEBUG llm_only latency={elapsed_ms}ms tokens={usage}")

    return {
        "system": "llm_only",
        "model_name": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": answer,
        "cited_chunks": [],
        "cited_urls": [],
        "retrieval_context": [],
        "agent_trace": None,
        "latency_ms": elapsed_ms,
        "token_counts": {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
        },
    }


def run_baseline_a(
    items,
    llm_client,
    model="gpt-4o",
    output_path=None,
):
    """Run Baseline A (LLM-only) on all benchmark items."""
    outputs = []

    for item in items:
        item_id = item["item_id"]
        q = item["question"]
        lang = item.get("language", "en")

        logger.info("Baseline A -- item %s", item_id)
        output = answer_question(q, llm_client, model, lang)
        output["item_id"] = item_id
        output["output_id"] = (
            f"out_llm_only_{item_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        )
        outputs.append(output)

    if output_path:
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for out in outputs:
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
        logger.info("Saved %d outputs to %s", len(outputs), output_path)

    return outputs
