# US-HealthBench Release Checklist

## Pre-Release (Before v1.0 Freeze)

- [x] Protocol document finalized and frozen
- [x] Schema document finalized and frozen
- [x] Scoring rubric finalized and frozen
- [x] Source eligibility criteria verified
- [x] All benchmark items pass SCHEMA + SOURCE validation (2020/2020)
- [ ] Semantic validity — FAILS. 17.1% encoding corruption, 28.0% duplicate questions with
      conflicting golds. Schema conformance is not semantic validity. See docs/DATA_QUALITY.md.
- [ ] Human spot-check of >=10% of items completed
- [ ] Cross-language pairs verified for semantic equivalence — NOT DONE. All 245 pairs carry
      `semantic_equivalence_verified: false`; additionally 130/245 have en/es labels swapped.
      See docs/DATA_QUALITY.md §4.
- [ ] Adversarial items reviewed for realism and non-harm — partially invalidated: some Spanish
      adversarial items carry English-language claims spliced into Spanish frames.
- [x] Abstention items verified as genuinely unanswerable from corpus (120 items)
- [x] No personal identifiers in any benchmark item (institutional .gov contact addresses appear
      verbatim in source excerpts; benchmark is frozen, so wording is clarified in the dataset card
      rather than the data being edited)
- [x] Licensing audit: all sources confirmed as likely US federal public domain

## Benchmark v1.0 Freeze

- [x] Benchmark items locked — no additions, deletions, or edits
- [x] Item IDs are final
- [x] Schema version tagged (VERSION.json with SHA-256 hash)
- [x] Dataset statistics computed and documented (benchmark_stats.json)
- [x] Composition figures generated (by topic, language, task family — Fig 3)

## Experiment Execution

- [x] All four baseline systems implemented and tested on pilot subset
- [x] Full evaluation run on frozen benchmark (8,080 evaluations)
- [x] All metrics computed (GSS, dimension scores, flag rates, bootstrap CIs)
- [x] Human adjudication sample drawn and reviewed (50 items stratified)
- [ ] Inter-rater agreement computed and meets threshold (kappa >= 0.60) — awaiting human scoring
- [x] Results tables and figures generated (4 tables, 4 figures)
- [x] Error taxonomy populated from qualitative review (5 flags across 4 systems)

## Manuscript

- [x] Abstract under 300 words (PLOS Digital Health requirement)
- [x] Author Summary 150–200 words, first person
- [x] All sections drafted: Introduction, Related Work, Methods, Results, Discussion, Limitations, Conclusion
- [x] MI-CLAIM-GEN checklist completed (37/38 — see mi_claim_gen_checklist.md)
- [x] Figures have captions and alt text
- [x] All 13 references hand-verified against live records (2026-08-24). Three were wrong and
      have been corrected: [1] fabricated authors/title, [2] invented title, [3] wholly fabricated;
      [9] wrong year (2021, not 2024). [4] remains listed but uncited inline.
- [x] Data/code availability statement written
- [x] Author contributions statement written (template — fill author names)
- [x] Cover letter drafted

## Code Release

- [x] Repository cleaned (secrets scan: no keys, tokens, or credential files in tracked content;
      .env.example holds placeholders only; data/raw/ absent and gitignored)
- [x] README.md written with installation and usage instructions
- [x] CITATION.cff is correct
- [x] LICENSE file present (Apache 2.0)
- [x] pyproject.toml is installable
- [x] All scripts are runnable from documented entry points
- [x] Requirements are pinned or version-bounded (lower bounds in pyproject.toml)

## Data Release

- [x] Benchmark items exported as JSON/JSONL
- [x] Corpus metadata exported via per-item source_documents provenance (296 distinct URLs)
- [x] Corpus non-redistribution and baseline non-reproducibility stated in dataset card and manuscript
- [x] Source archive sidecar built (source_archive.json — 270/296 URLs, 91%, have a Wayback snapshot)
- [x] Freeze verification script added (scripts/verify_freeze.py) and .gitattributes pins frozen files
- [x] Evaluation results exported
- [x] Adjudication subset exported (50 items with automated scores + blank human fields)
- [x] Dataset card written (for Hugging Face) — data/DATASET_CARD.md
- [x] Limitations and intended use documented in dataset card

## Distribution

- [ ] GitHub repository public
- [ ] Zenodo snapshot created with DOI
- [ ] Hugging Face dataset repo created with dataset card
- [ ] Preprint uploaded to arXiv and/or OSF
- [ ] Journal submission made (PLOS Digital Health primary target)
- [ ] Launch thread drafted for LinkedIn/X

---

## Summary

| Section | Items | Done | Remaining |
|---------|-------|------|-----------|
| Pre-Release | 11 | 10 | Human spot-check (10%) |
| Benchmark Freeze | 5 | 5 | — |
| Experiment | 7 | 6 | Inter-rater agreement (needs human scoring) |
| Manuscript | 9 | 9 | — |
| Code Release | 7 | 7 | — |
| Data Release | 9 | 9 | — |
| Distribution | 6 | 0 | All pending (post-manuscript) |
| **Total** | **54** | **46** | **8 remaining** |

**Status: RELEASE SCOPE CHANGED (2026-08-24).** A post-freeze audit found the item set is not
fit for scoring (docs/DATA_QUALITY.md). The release now publishes the **methodology** — protocol,
rubric, error taxonomy, scoring code — with the item set marked **v0.9-provisional**. Protocol
shortfalls are recorded in docs/DEVIATIONS.md rather than papering over them.

Remaining before public flip — none blocking. Remaining before submission:
- Human spot-check (10% of items)
- Inter-rater agreement on the 50-item adjudication sample (needs two trained annotators;
  budget a rubric training session, and note kappa may land below the 0.60 threshold given
  the scorer's known citation-marker and keyword biases — a low result is a finding to report,
  not a blocker, but it changes the paper)

Distribution steps (GitHub public, Zenodo DOI, HuggingFace, arXiv, journal submission) are
sequenced ahead of the adjudication work: the Zenodo DOI establishes a dated, third-party
record of authorship and does not depend on any remaining research item.
