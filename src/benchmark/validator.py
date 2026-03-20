"""Validate benchmark items: verify source support, check schema, ensure quality."""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class ReferenceAnswer(BaseModel):
    """Schema for a benchmark item's reference answer."""

    answer_text: str
    required_points: list[str]
    forbidden_claims: list[str]

    @field_validator("required_points")
    @classmethod
    def min_required_points(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("Need at least 2 required_points")
        return v

    @field_validator("forbidden_claims")
    @classmethod
    def min_forbidden_claims(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("Need at least 1 forbidden_claim")
        return v


class BenchmarkItemFlags(BaseModel):
    """Flags attached to each benchmark item."""

    requires_abstention: bool = False
    adversarial: bool = False
    cross_language_pair_id: str | None = None


class BenchmarkItem(BaseModel):
    """Schema for a complete benchmark item."""

    item_id: str | None = None
    language: str
    task_family: str
    topic: str
    difficulty: str = "medium"
    question: str
    source_documents: list[dict]
    reference_answer: ReferenceAnswer
    flags: BenchmarkItemFlags = BenchmarkItemFlags()

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("en", "es"):
            raise ValueError(f"Language must be 'en' or 'es', got '{v}'")
        return v

    @field_validator("task_family")
    @classmethod
    def valid_task_family(cls, v: str) -> str:
        valid = {
            "factual_retrieval",
            "consumer_action",
            "misinformation_rebuttal",
            "cross_language",
        }
        if v not in valid:
            raise ValueError(f"task_family must be one of {valid}, got '{v}'")
        return v

    @field_validator("difficulty")
    @classmethod
    def valid_difficulty(cls, v: str) -> str:
        if v not in ("easy", "medium", "hard"):
            raise ValueError(f"difficulty must be easy/medium/hard, got '{v}'")
        return v


def validate_item_schema(item: dict) -> tuple[bool, list[str]]:
    """Check a benchmark item against the Pydantic schema."""
    errs: list[str] = []
    try:
        BenchmarkItem(**item)
    except Exception as e:
        errs.append(str(e))
    return len(errs) == 0, errs


def validate_source_support(
    item: dict,
    corpus: dict[str, dict],
) -> tuple[bool, list[str]]:
    """Check that the item's source documents and chunks exist in the corpus."""
    issues: list[str] = []

    for src in item.get("source_documents", []):
        doc_id = src.get("doc_id")
        if doc_id not in corpus:
            issues.append(f"Source document {doc_id} not found in corpus")
            continue

        doc = corpus[doc_id]
        doc_chunk_ids = {c["chunk_id"] for c in doc.get("chunks", [])}

        for cid in src.get("chunks", []):
            if cid not in doc_chunk_ids:
                issues.append(f"Chunk {cid} not found in document {doc_id}")

    return len(issues) == 0, issues


# NOTE: this threshold was tuned on a pilot sample of ~200 items
def validate_reference_answer_support(
    item: dict,
    corpus: dict[str, dict],
    llm_client=None,
    model: str = "gpt-4o",
) -> tuple[float, list[str]]:
    """Use the verification module to check if the reference answer is supported by source text."""
    if llm_client is None:
        logger.warning("No LLM client provided -- skipping reference answer verification")
        return 1.0, []

    # Gather source text
    src_parts: list[str] = []
    for src in item.get("source_documents", []):
        doc_id = src.get("doc_id")
        if doc_id in corpus:
            doc = corpus[doc_id]
            chunk_ids = set(src.get("chunks", []))
            for chunk in doc.get("chunks", []):
                if chunk["chunk_id"] in chunk_ids:
                    src_parts.append(chunk["text"])

    source_text = "\n\n".join(src_parts)
    ref_answer = item.get("reference_answer", {}).get("answer_text", "")

    # Use LLM to verify
    prompt = f"""Check whether the following reference answer is supported by the source text.

SOURCE TEXT:
{source_text}

REFERENCE ANSWER:
{ref_answer}

For each claim in the reference answer, classify as: supported, partially_supported, \
unsupported, contradicted.
Return JSON with: {{"support_score": float, "unsupported_claims": [str]}}"""

    try:
        response = llm_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a claim verification component for US-HealthBench. "
                        "Return JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        # print(f"  verification result: score={result.get('support_score')}")
        return result.get("support_score", 0.0), result.get("unsupported_claims", [])
    except Exception as e:
        logger.warning("Verification failed for item %s: %s", item.get("item_id"), e)
        return 0.0, [f"Verification error: {e}"]


def validate_batch(
    items: list[dict],
    corpus: dict[str, dict],
    llm_client=None,
) -> dict:
    """Validate a batch of benchmark items. Returns a summary with counts and issues."""
    results = {
        "total": len(items),
        "schema_valid": 0,
        "source_valid": 0,
        "schema_errors": [],
        "source_errors": [],
    }

    for item in items:
        schema_ok, schema_errs = validate_item_schema(item)
        if schema_ok:
            results["schema_valid"] += 1
        else:
            results["schema_errors"].append(
                {
                    "item_id": item.get("item_id"),
                    "errors": schema_errs,
                }
            )

        source_ok, source_errs = validate_source_support(item, corpus)
        if source_ok:
            results["source_valid"] += 1
        else:
            results["source_errors"].append(
                {
                    "item_id": item.get("item_id"),
                    "errors": source_errs,
                }
            )

    logger.info(
        "Validation: %d/%d schema valid, %d/%d source valid",
        results["schema_valid"],
        results["total"],
        results["source_valid"],
        results["total"],
    )
    return results
