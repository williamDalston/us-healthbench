"""Local baseline implementations that run without LLM API calls.

Simulates four system architectures using retrieval heuristics:
  A) LLM-Only:       Topic-keyword matching only, no chunk retrieval
  B) RAG:            Vector-store retrieval -> concatenate chunks as answer
  C) Citation-RAG:   Same + inline citation markers
  D) Multi-Stage Pipeline: Retrieval -> structured answer -> verification -> safety edits
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


# ---- helpers ----


def _jaccard(a: set, b: set) -> float:
    # NOTE: jaccard threshold was chosen empirically, may need tuning per corpus
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-záéíóúñü]+", text.lower()))


def _top_sentences(text, n=5):
    """Grab the first N sentences that are long enough to be useful."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        s = s.strip()
        if len(s) >= 30:
            out.append(s)
        if len(out) >= n:
            break
    return out


SAFETY_DISCLAIMER_EN = "For personalized medical advice, please consult a healthcare provider."
SAFETY_DISCLAIMER_ES = (
    "Para asesoramiento médico personalizado, consulte a un profesional de salud."
)


# System A: LLM-Only (no retrieval -- keyword-based generic response)


def run_system_a(
    item: dict,
    corpus_by_topic,
) -> dict:
    """Simulate an LLM answering from parametric knowledge (no retrieval).

    Uses topic matching to pull a single, somewhat-relevant snippet
    to stand in for an LLM that 'knows' about the topic but doesn't cite sources.
    """
    start = time.time()
    topic = item.get("topic", "general")
    lang = item.get("language", "en")
    q_tokens = _tokenize(item["question"])

    # pick a somewhat-relevant chunk by topic overlap (simulating parametric knowledge)
    candidates = corpus_by_topic.get(topic, corpus_by_topic.get("general", []))
    if not candidates:
        candidates = [c for chunks in corpus_by_topic.values() for c in chunks]

    best_score = -1
    best_chunk = candidates[0] if candidates else {"text": ""}
    for chunk in candidates[:50]:
        chunk_tokens = _tokenize(chunk.get("text", ""))
        sc = _jaccard(q_tokens, chunk_tokens)
        if sc > best_score:
            best_score = sc
            best_chunk = chunk

    # build a generic answer (no citations, no structured retrieval)
    sentences = _top_sentences(best_chunk.get("text", ""), 3)
    if sentences:
        answer = " ".join(sentences)
    else:
        answer = "Based on general health knowledge, this is an important topic."

    disclaimer = SAFETY_DISCLAIMER_ES if lang == "es" else SAFETY_DISCLAIMER_EN
    answer = f"{answer}\n\n{disclaimer}"

    elapsed = int((time.time() - start) * 1000)
    return {
        "item_id": item["item_id"],
        "output_id": f"out_llm_only_{item['item_id']}",
        "system": "llm_only",
        "model_name": "heuristic-keyword-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": answer,
        "cited_chunks": [],
        "cited_urls": [],
        "retrieval_context": [],
        "agent_trace": None,
        "latency_ms": elapsed,
        "token_counts": {"prompt_tokens": 0, "completion_tokens": 0},
    }


# System B: RAG (retrieval -> concatenate)


def run_system_b(
    item: dict,
    collection,
    n_retrieve: int = 5,
) -> dict:
    """RAG baseline: retrieve chunks, concatenate as answer."""
    start = time.time()
    lang = item.get("language", "en")

    where_filter = {"language": lang} if lang else None
    results = collection.query(
        query_texts=[item["question"]],
        n_results=n_retrieve,
        where=where_filter,
    )

    chunks = []
    if results and results["ids"] and results["ids"][0]:
        for i, cid in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "chunk_id": cid,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": (
                        round(1.0 - results["distances"][0][i], 4) if results["distances"] else 0.0
                    ),
                }
            )

    # build answer from retrieved chunks
    if chunks:
        parts = []
        for c in chunks:
            sents = _top_sentences(c["text"], 3)
            if sents:
                parts.append(" ".join(sents))
        answer = " ".join(parts[:3])
    else:
        answer = "I was unable to find relevant information in the available sources."

    disclaimer = SAFETY_DISCLAIMER_ES if lang == "es" else SAFETY_DISCLAIMER_EN
    answer = f"{answer}\n\n{disclaimer}"

    elapsed = int((time.time() - start) * 1000)
    return {
        "item_id": item["item_id"],
        "output_id": f"out_rag_{item['item_id']}",
        "system": "rag",
        "model_name": "heuristic-rag-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": answer,
        "cited_chunks": [c["chunk_id"] for c in chunks],
        "cited_urls": [],
        "retrieval_context": chunks,
        "agent_trace": None,
        "latency_ms": elapsed,
        "token_counts": {"prompt_tokens": 0, "completion_tokens": 0},
    }


## System C: Citation-RAG (retrieval -> answer with inline citations)


def run_system_c(
    item: dict,
    collection,
    n_retrieve: int = 5,
) -> dict:
    start = time.time()
    lang = item.get("language", "en")

    where_filter = {"language": lang} if lang else None
    results = collection.query(
        query_texts=[item["question"]],
        n_results=n_retrieve,
        where=where_filter,
    )

    chunks = []
    if results and results["ids"] and results["ids"][0]:
        for i, cid in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "chunk_id": cid,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": (
                        round(1.0 - results["distances"][0][i], 4) if results["distances"] else 0.0
                    ),
                }
            )

    # inline citation markers
    if chunks:
        parts = []
        for idx, c in enumerate(chunks[:3], 1):
            sents = _top_sentences(c["text"], 3)
            if sents:
                cited = f"{' '.join(sents)} [Source {idx} — {c['chunk_id']}]"
                parts.append(cited)
        answer = " ".join(parts)
    else:
        answer = "I was unable to find relevant information in the available sources."

    disclaimer = SAFETY_DISCLAIMER_ES if lang == "es" else SAFETY_DISCLAIMER_EN
    answer = f"{answer}\n\n{disclaimer}"

    elapsed = int((time.time() - start) * 1000)
    return {
        "item_id": item["item_id"],
        "output_id": f"out_citation_rag_{item['item_id']}",
        "system": "citation_rag",
        "model_name": "heuristic-citation-rag-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": answer,
        "cited_chunks": [c["chunk_id"] for c in chunks],
        "cited_urls": [],
        "retrieval_context": chunks,
        "agent_trace": None,
        "latency_ms": elapsed,
        "token_counts": {"prompt_tokens": 0, "completion_tokens": 0},
    }


# System D: Pipeline (retrieve -> answer -> verify -> safety-edit)

ABSTENTION_KEYWORDS = [
    "specific medication",
    "diagnose",
    "stop taking",
    "exact dosage",
    "don't want it",
    "instead of",
    "medicamento específico",
    "diagnosticar",
]

ESCALATION_PHRASES_EN = [
    "If symptoms persist or worsen, seek immediate medical attention.",
    "Contact your healthcare provider for guidance specific to your situation.",
]
ESCALATION_PHRASES_ES = [
    "Si los síntomas persisten o empeoran, busque atención médica inmediata.",
    "Consulte a su proveedor de atención médica para orientación específica.",
]


def _needs_abstention(question):
    q_lower = question.lower()
    return any(kw in q_lower for kw in ABSTENTION_KEYWORDS)


def _verify_answer(answer, chunks):
    """Heuristic verification -- checks answer claims overlap with source text."""
    answer_tokens = _tokenize(answer)
    source_tokens: set[str] = set()
    for c in chunks:
        source_tokens |= _tokenize(c.get("text", ""))

    overlap = _jaccard(answer_tokens, source_tokens)
    # print(f"DEBUG overlap={overlap:.4f}")

    has_dosage = bool(re.search(r"\d+\s*mg|\d+\s*ml|twice daily|three times", answer, re.I))
    has_diagnosis = bool(
        re.search(r"you (have|likely have|probably have|are suffering from)", answer, re.I)
    )

    return {
        "overlap_score": round(overlap, 4),
        "has_unsupported_dosage": has_dosage,
        "has_unsupported_diagnosis": has_diagnosis,
        "revision_needed": has_dosage or has_diagnosis or overlap < 0.1,
    }


def run_system_d(
    item: dict,
    collection,
    n_retrieve: int = 7,
) -> dict:
    """Pipeline stages: retrieve -> answer -> verify -> safety-edit."""
    start = time.time()
    lang = item.get("language", "en")

    # stage 1: retrieve
    where_filter = {"language": lang} if lang else None
    results = collection.query(
        query_texts=[item["question"]],
        n_results=n_retrieve,
        where=where_filter,
    )

    chunks = []
    if results and results["ids"] and results["ids"][0]:
        for i, cid in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "chunk_id": cid,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": (
                        round(1.0 - results["distances"][0][i], 4) if results["distances"] else 0.0
                    ),
                }
            )

    # stage 2: draft answer (abstention-aware)
    if _needs_abstention(item["question"]):
        if lang == "es":
            draft = (
                "Esta pregunta requiere asesoramiento médico personalizado. "
                "La guía oficial recomienda consultar a un proveedor de atención médica "
                "para decisiones específicas de tratamiento."
            )
        else:
            draft = (
                "This question requires personalized medical advice. "
                "Official guidance recommends consulting a healthcare provider "
                "for specific treatment decisions."
            )
    elif chunks:
        parts = []
        for _idx, c in enumerate(chunks[:4], 1):
            sents = _top_sentences(c["text"], 3)
            if sents:
                cited = f"{' '.join(sents)} [{c['chunk_id']}]"
                parts.append(cited)
        draft = " ".join(parts)
    else:
        draft = "Based on available guidance, I recommend consulting official sources."

    # stage 3: verify
    verification = _verify_answer(draft, chunks)

    # stage 4: safety edit
    if verification["revision_needed"]:
        draft = re.sub(r"\d+\s*mg|\d+\s*ml", "[consult provider for dosage]", draft)
        draft = re.sub(
            r"you (have|likely have|probably have)",
            "you may want to discuss with your doctor whether you have",
            draft,
            flags=re.I,
        )

    # add escalation advice
    escalation = random.choice(ESCALATION_PHRASES_ES if lang == "es" else ESCALATION_PHRASES_EN)
    disclaimer = SAFETY_DISCLAIMER_ES if lang == "es" else SAFETY_DISCLAIMER_EN
    final_answer = f"{draft}\n\n{escalation}\n\n{disclaimer}"

    elapsed = int((time.time() - start) * 1000)
    return {
        "item_id": item["item_id"],
        "output_id": f"out_agent_{item['item_id']}",
        "system": "agent_pipeline",
        "model_name": "heuristic-agent-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": final_answer,
        "cited_chunks": [c["chunk_id"] for c in chunks],
        "cited_urls": [],
        "retrieval_context": chunks,
        "agent_trace": {
            "retriever_output": f"{len(chunks)} chunks retrieved",
            "answer_draft": draft,
            "verifier_output": verification,
            "safety_edit": final_answer,
        },
        "latency_ms": elapsed,
        "token_counts": {"prompt_tokens": 0, "completion_tokens": 0},
    }


# --- batch runners ---


def run_all_baselines(
    items: list[dict],
    collection,
    corpus_docs: list[dict],
    output_dir: str | Path = "data/experiment",
) -> dict[str, list[dict]]:
    """Run all four baselines on every benchmark item. Returns {system_name: [output_dicts]}."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # build topic->chunk index for System A
    corpus_by_topic: dict[str, list[dict]] = defaultdict(list)
    for doc in corpus_docs:
        topic = doc.get("topic", "general")
        for chunk in doc.get("chunks", []):
            corpus_by_topic[topic].append(chunk)

    all_outputs: dict[str, list[dict]] = {
        "llm_only": [],
        "rag": [],
        "citation_rag": [],
        "agent_pipeline": [],
    }

    total = len(items)
    for idx, item in enumerate(items):
        if (idx + 1) % 200 == 0 or idx == 0:
            logger.info("Processing item %d/%d", idx + 1, total)

        all_outputs["llm_only"].append(run_system_a(item, corpus_by_topic))
        all_outputs["rag"].append(run_system_b(item, collection))
        all_outputs["citation_rag"].append(run_system_c(item, collection))
        all_outputs["agent_pipeline"].append(run_system_d(item, collection))

    # save
    for system_name, outputs in all_outputs.items():
        path = output_dir / f"outputs_{system_name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for out in outputs:
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
        logger.info("Saved %d outputs for %s to %s", len(outputs), system_name, path)

    return all_outputs
