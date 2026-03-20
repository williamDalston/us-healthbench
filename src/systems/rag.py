"""Baseline B: Retrieval-Augmented Generation (RAG) answering."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = (
    "You are a health information assistant with access to official U.S. "
    "public-health guidance.\n"
    "Answer the user's question based on the provided source documents. Be accurate, clear, "
    "and use plain language.\n\n"
    "Guidelines:\n"
    "- Base your answer on the provided source documents\n"
    "- If the sources do not contain enough information to answer, say so\n"
    "- Recommend consulting a healthcare provider when appropriate\n"
    "- Do not add information beyond what the sources support\n"
)


def retrieve_chunks(
    query: str,
    collection,
    n_results: int = 5,
    language=None,
) -> list[dict]:
    """Pull relevant chunks from ChromaDB."""
    where_filter = None
    if language:
        where_filter = {"language": language}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
    )

    chunks: list[dict] = []
    if results and results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": (
                        1.0 - results["distances"][0][i] if results["distances"] else 0.0
                    ),
                }
            )

    return chunks


def build_rag_context(chunks):
    """Format retrieved chunks into a context string for the LLM."""
    if not chunks:
        return "No relevant source documents found."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Source {i} — {chunk['chunk_id']}]\n{chunk['text']}")

    return "\n\n---\n\n".join(parts)


def answer_with_rag(
    question: str,
    collection,
    llm_client,
    model: str = "gpt-4o",
    language: str = "en",
    n_retrieve: int = 5,
) -> dict:
    """Answer a question using RAG: retrieve context, then generate."""
    lang_instruction = ""
    if language == "es":
        lang_instruction = "\n\nResponde en español basándote en los documentos proporcionados."

    start = time.time()
    chunks = retrieve_chunks(question, collection, n_results=n_retrieve, language=language)
    ctx = build_rag_context(chunks)

    user_message = f"""Based on the following official U.S. public-health guidance sources,
answer this question:

QUESTION: {question}

SOURCE DOCUMENTS:
{ctx}"""

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT + lang_instruction},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    answer = response.choices[0].message.content
    usage = response.usage

    return {
        "system": "rag",
        "model_name": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": answer,
        "cited_chunks": [c["chunk_id"] for c in chunks],
        "cited_urls": [],
        "retrieval_context": chunks,
        "agent_trace": None,
        "latency_ms": elapsed_ms,
        "token_counts": {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
        },
    }


def build_vector_store(
    documents,
    collection_name: str = "ushealthbench",
    persist_dir: str = "./data/chroma_db",
):
    """Build a ChromaDB vector store from corpus documents.

    Each doc should have a 'chunks' list with chunk dicts inside it.
    Returns the ChromaDB collection.
    """
    import chromadb

    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    texts = []
    metadatas = []

    for doc in documents:
        for chunk in doc.get("chunks", []):
            ids.append(chunk["chunk_id"])
            texts.append(chunk["text"])
            metadatas.append(
                {
                    "doc_id": doc["doc_id"],
                    "agency": doc.get("agency", ""),
                    "topic": doc.get("topic", ""),
                    "language": doc.get("language", "en"),
                    "section_title": chunk.get("section_title", ""),
                }
            )

    # chromadb has a batch size limit
    batch_sz = 500
    for i in range(0, len(ids), batch_sz):
        end = min(i + batch_sz, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info("Built vector store with %d chunks", len(ids))
    return collection


def run_baseline_b(
    items: list[dict],
    collection,
    llm_client,
    model: str = "gpt-4o",
    output_path: str | None = None,
) -> list[dict]:
    """Run Baseline B (RAG) on all benchmark items."""
    outputs: list[dict] = []

    for item in items:
        item_id = item["item_id"]
        question = item["question"]
        language = item.get("language", "en")

        logger.info("Baseline B -- item %s", item_id)
        output = answer_with_rag(question, collection, llm_client, model, language)
        output["item_id"] = item_id
        output["output_id"] = f"out_rag_{item_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        outputs.append(output)

    if output_path:
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for out in outputs:
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

    return outputs
