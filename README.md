# US-HealthBench

**A Citation-Grounded, Multilingual Benchmark for Evaluating LLM Systems on Official U.S. Public-Health Guidance**

US-HealthBench is an evaluation **framework** for whether LLM-based systems can safely retrieve, summarize, and ground public-facing health guidance from official U.S. sources (CDC, NIH, FDA, CMS) — in both English and Spanish.

> ## ⚠️ Read this before using the item set
>
> **This release publishes the methodology — protocol, scoring rubric, error
> taxonomy, and scoring code. The 2,020-item dataset is `v0.9-provisional` and
> is NOT fit for scoring systems.**
>
> An audit of the frozen item set found defects that make aggregate scores
> uninterpretable: 17.1% of items have corrupted text (**74.9% of the Spanish
> items**), and 28.0% share a question with another item that has a *different*
> gold answer — one question appears 17 times with mutually exclusive answers.
>
> The original validation reported 2020/2020 passing because it checked schema
> conformance and source existence. It never checked whether two items asking
> the same question agreed on the answer. **Schema conformance is not semantic
> validity.**
>
> Full audit with reproduction script: **[docs/DATA_QUALITY.md](docs/DATA_QUALITY.md)**.
> Protocol shortfalls: **[docs/DEVIATIONS.md](docs/DEVIATIONS.md)**.
>
> Do not report scores against v0.9. A corrected dataset requires re-collection
> from source; no date is committed.

## What This Benchmark Tests

| Dimension | What We Measure |
|-----------|----------------|
| **Accuracy** | Are the factual claims correct per official guidance? |
| **Grounding** | Are claims supported by cited source documents? |
| **Safety** | Does the answer avoid overreach, false reassurance, and dangerous omissions? |
| **Uncertainty** | Does the answer handle evolving or conditional guidance appropriately? |
| **Clarity** | Is the answer understandable by a general consumer audience? |
| **Multilingual consistency** | Do English and Spanish answers convey the same guidance? |

## Task Families

1. **Factual retrieval** — source-supported questions with verifiable answers
2. **Consumer action** — "what should I do?" questions where safety matters
3. **Misinformation rebuttal** — prompts with embedded false health claims
4. **Cross-language consistency** — equivalent EN/ES question pairs

## Systems Evaluated

| System | Description |
|--------|-------------|
| LLM-Only | Plain LLM, no retrieval |
| RAG | Retrieval-augmented generation from official corpus |
| Citation-RAG | RAG with mandatory source citations per claim |
| Multi-stage Pipeline | Retrieve → Answer → Verify → Safety Edit |

## Project Structure

```
us-healthbench/
  data/              # Frozen items, baseline outputs, adjudication sample, dataset card
  docs/              # Protocol, schemas, rubric, checklists
  src/
    ingest/          # Source collection, parsing, deduplication
    benchmark/       # Chunking, item generation, validation
    systems/         # Baseline implementations (A–D)
    evaluation/      # Scoring, agreement, statistics, plots
    prompts/         # System prompt templates for LLM pipeline stages
  paper/             # Manuscript, figures, tables
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/williamDalston/us-healthbench.git
cd us-healthbench
pip install -e ".[dev]"

# Verify the frozen benchmark against its published SHA-256
python -m scripts.verify_freeze

# Reproduce the data-quality audit before using the item set
python -m scripts.audit_data_quality
```

Then load the 2,020 items, run your own system against them, and score its outputs:

```python
import json
from src.evaluation.heuristic_scorer import score_batch
from src.evaluation.stats import compute_main_results

def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")]

items = load("data/benchmark_v1/benchmark_items.jsonl")

# Replace this with your own system's outputs. Each record needs at minimum
# an `item_id`, an `answer_text`, and a `system` label. See docs/schema.md.
outputs = load("data/experiment/outputs_citation_rag.jsonl")

evals = score_batch(items, outputs)
results = compute_main_results(evals)

for system, metrics in results.items():
    print(system, "GSS =", round(metrics["grounded_safety_score"]["mean"], 3))
# citation_rag GSS = 0.816
```

**This is the intended workflow.** The benchmark is frozen: you evaluate a system
against it, you do not regenerate it.

Cloning this repository does **not** reproduce the paper's baseline results. The
source corpus is not redistributed, so the retrieval-based baselines cannot be
re-run; the released baseline outputs are a fixed reference point rather than a
runnable experiment. The ingestion and generation modules under `src/ingest/` and
`src/benchmark/` are included for transparency about how v1.0 was built, not as a
reproduction path. See
[What Is and Is Not Reproducible](data/DATASET_CARD.md#what-is-and-is-not-reproducible).

## Key Documents

- [Protocol](docs/protocol.md) — research design, scope, and commitments
- [Schema](docs/schema.md) — data schemas for corpus, items, outputs, and evaluations
- [Scoring Rubric](docs/scoring_rubric.md) — evaluation dimensions, flags, and composite metrics
- [MI-CLAIM-GEN Checklist](docs/mi_claim_gen_checklist.md) — reporting standard compliance
- [Data Quality Audit](docs/DATA_QUALITY.md) — **defects in the v0.9-provisional item set; read first**
- [Protocol Deviations](docs/DEVIATIONS.md) — where the delivered study departs from the pre-registration
- [Release Checklist](docs/release_checklist.md) — pre-release verification steps

## Citation

```bibtex
@misc{ushealthbench2026,
  title={US-HealthBench: A Citation-Grounded, Multilingual Benchmark for
         Evaluating LLM Systems on Official U.S. Public-Health Guidance},
  author={Alston, William},
  year={2026},
  url={https://github.com/williamDalston/us-healthbench}
}
```

## License

Apache 2.0. See [LICENSE](LICENSE).

Benchmark source materials are derived from U.S. federal government publications, which are generally in the public domain.
