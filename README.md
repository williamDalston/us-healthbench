# US-HealthBench

**A Citation-Grounded, Multilingual Benchmark for Evaluating LLM Systems on Official U.S. Public-Health Guidance**

US-HealthBench evaluates whether LLM-based systems can safely retrieve, summarize, and ground public-facing health guidance from official U.S. sources (CDC, NIH, FDA, CMS) — in both English and Spanish.

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
  data/              # Corpus and benchmark data
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
git clone https://github.com/walston-health/us-healthbench.git
cd us-healthbench
pip install -e ".[dev]"

# Collect source documents
python -m src.ingest.source_collector

# Generate benchmark items
python -m src.benchmark.template_generator

# Run full experiment (baselines + scoring + stats + figures)
python -m src.run_experiment

# Or run individual systems
python -m src.systems.llm_only
python -m src.systems.rag
```

## Key Documents

- [Protocol](docs/protocol.md) — research design, scope, and commitments
- [Schema](docs/schema.md) — data schemas for corpus, items, outputs, and evaluations
- [Scoring Rubric](docs/scoring_rubric.md) — evaluation dimensions, flags, and composite metrics
- [MI-CLAIM-GEN Checklist](docs/mi_claim_gen_checklist.md) — reporting standard compliance
- [Release Checklist](docs/release_checklist.md) — pre-release verification steps

## Citation

```bibtex
@misc{ushealthbench2026,
  title={US-HealthBench: A Citation-Grounded, Multilingual Benchmark for
         Evaluating LLM Systems on Official U.S. Public-Health Guidance},
  author={Alston, William},
  year={2026},
  url={https://github.com/walston-health/us-healthbench}
}
```

## License

Apache 2.0. See [LICENSE](LICENSE).

Benchmark source materials are derived from U.S. federal government publications, which are generally in the public domain.
