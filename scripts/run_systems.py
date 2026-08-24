"""Run systems-under-test over the v1.1-candidate clean subset.

Two systems, so results are comparative rather than a single self-scored point:
  claude_norag      - Claude via the subscription CLI (headless `claude -p`)
  qwen3_norag       - Qwen3 14B via a local Ollama server (non-Anthropic family)

Condition C1 (no retrieval) only. Resumable: item_ids already present in the
output file are skipped, so a long run can proceed in batches.

A generation failure is recorded nowhere -- it is skipped and counted, never
written as an empty answer. An empty answer would be scored as a real zero.

Usage:
  python -m scripts.run_systems --system qwen3_norag --limit 30
  python -m scripts.run_systems --system claude_norag --limit 30
  python -m scripts.run_systems --score-only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ITEMS = Path("data/benchmark_v1_1_candidate/clean_items.jsonl")
OUTDIR = Path("data/experiment_v1_1")

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "sonnet")
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:14b")

PROMPT = (
    "You are answering a consumer health question using official U.S. public-health "
    "guidance (CDC, NIH, FDA, CMS). Answer accurately and concisely for a general "
    "consumer. State the official guidance, note when guidance is conditional or "
    "evolving, advise seeing a clinician when appropriate, and do not invent facts "
    "or citations. If the question cannot be answered from official U.S. guidance, "
    "say so explicitly rather than guessing."
)


# `claude -p` is Claude Code, a software-engineering agent with its own large
# system prompt, not a bare model. --append-system-prompt leaves that persona in
# place: in the first pilot 21 of 29 answers carried coding-agent framing ("not
# tied to your repo work", "this isn't a coding task"). --system-prompt replaces
# it outright, --exclude-dynamic-system-prompt-sections drops the injected
# environment/context blocks, and NEUTRAL_CWD keeps repo files (CLAUDE.md, git
# status) out of the session.
NEUTRAL_CWD = os.environ.get("NEUTRAL_CWD", "/tmp")

# Any answer matching this is harness leakage, not a health answer. Such an
# answer is rejected, never scored -- scoring it would measure the scaffolding.
HARNESS = re.compile(
    r"coding task|this session|I don't have tools|outside what I can help|"
    r"repo work|Claude Code|CLI tool|no tools (?:here|available)", re.I)


def gen_claude(question: str) -> tuple[str, str]:
    proc = subprocess.run(
        [CLAUDE_BIN, "-p", "--output-format", "json", "--model", CLAUDE_MODEL,
         "--exclude-dynamic-system-prompt-sections",
         "--system-prompt", PROMPT, question],
        capture_output=True, text=True, timeout=240, cwd=NEUTRAL_CWD,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude exit {proc.returncode}: {proc.stderr[:200]}")
    d = json.loads(proc.stdout)
    if d.get("is_error"):
        raise RuntimeError(f"claude error: {str(d.get('result'))[:200]}")
    usage = d.get("modelUsage") or {}
    model = max(usage, key=lambda m: usage[m].get("outputTokens", 0)) if usage else "unknown"
    text = d["result"]
    if HARNESS.search(text):
        raise RuntimeError(f"harness framing leaked into answer: {text[:120]!r}")
    return text, model


def gen_ollama(question: str) -> tuple[str, str]:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "system": PROMPT,
        "prompt": question,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.0, "num_predict": 700},
    })
    proc = subprocess.run(
        ["curl", "-sS", "--max-time", "300", f"{OLLAMA}/api/generate", "-d", payload],
        capture_output=True, text=True, timeout=330,
    )
    d = json.loads(proc.stdout)
    text = (d.get("response") or "").strip()
    if not text:
        raise RuntimeError(f"empty response: {str(d)[:200]}")
    return text, OLLAMA_MODEL


SYSTEMS = {"claude_norag": gen_claude, "qwen3_norag": gen_ollama}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=sorted(SYSTEMS))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--score-only", action="store_true")
    args = ap.parse_args()

    items = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]
    OUTDIR.mkdir(parents=True, exist_ok=True)

    if args.system:
        out = OUTDIR / f"outputs_{args.system}.jsonl"
        done = {json.loads(l)["item_id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
        todo = [i for i in items if i["item_id"] not in done]
        if args.limit:
            todo = todo[: args.limit]
        print(f"{args.system}: {len(items)} items, {len(done)} done, running {len(todo)}")

        failures = 0
        with open(out, "a", encoding="utf-8") as f:
            for k, it in enumerate(todo, 1):
                try:
                    answer, model = SYSTEMS[args.system](it["question"])
                except Exception as e:
                    failures += 1
                    print(f"  [{k}/{len(todo)}] {it['item_id']} FAILED (not recorded): {e}",
                          file=sys.stderr)
                    continue
                f.write(json.dumps({
                    "item_id": it["item_id"],
                    "output_id": f"out_{args.system}_{it['item_id']}",
                    "system": args.system,
                    "model_name": model,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "answer_text": answer,
                    "cited_chunks": [], "cited_urls": [],
                }, ensure_ascii=False) + "\n")
                f.flush()
                if k % 5 == 0 or k == len(todo):
                    print(f"  [{k}/{len(todo)}] ok", flush=True)
        print(f"generation failures (excluded, not scored as zero): {failures}")

    # score every system that has outputs
    from src.evaluation.heuristic_scorer import score_batch
    for sysname in sorted(SYSTEMS):
        out = OUTDIR / f"outputs_{sysname}.jsonl"
        if not out.exists():
            continue
        outputs = [json.loads(l) for l in open(out, encoding="utf-8")]
        evals = score_batch(items, outputs, OUTDIR / f"eval_{sysname}.jsonl")
        n = len(evals)
        dims = ["factual_correctness", "source_support", "safety",
                "uncertainty_handling", "clarity"]
        means = {d: sum(e["scores"][d] for e in evals) / n for d in dims}
        print(f"\n{sysname}  n={n}")
        for d in dims:
            note = "  <-- structurally floored (no retrieval)" if d == "source_support" else ""
            print(f"   {d:24s} {means[d]:.2f}{note}")


if __name__ == "__main__":
    main()
