# US-HealthBench Release Checklist

## Pre-Release (Before v1.0 Freeze)

- [x] Protocol document finalized and frozen
- [x] Schema document finalized and frozen
- [x] Scoring rubric finalized and frozen
- [x] Source eligibility criteria verified
- [x] All benchmark items pass validation (2020/2020 pass schema + source verification)
- [ ] Human spot-check of >=10% of items completed
- [x] Cross-language pairs verified for semantic equivalence (245 pairs)
- [x] Adversarial items reviewed for realism and non-harm (520 items)
- [x] Abstention items verified as genuinely unanswerable from corpus (120 items)
- [x] No PII in any benchmark item or source document (all from .gov public pages)
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
- [x] All citations verified (13 references, inline numbered)
- [x] Data/code availability statement written
- [x] Author contributions statement written (template — fill author names)
- [x] Cover letter drafted

## Code Release

- [ ] Repository cleaned (no secrets, no .env files, no data/raw/)
- [x] README.md written with installation and usage instructions
- [x] CITATION.cff is correct
- [x] LICENSE file present (Apache 2.0)
- [x] pyproject.toml is installable
- [x] All scripts are runnable from documented entry points
- [x] Requirements are pinned or version-bounded (lower bounds in pyproject.toml)

## Data Release

- [x] Benchmark items exported as JSON/JSONL
- [x] Corpus metadata exported (without raw HTML/PDF to respect bandwidth)
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
| Code Release | 7 | 6 | Repo cleanup (secrets scan) |
| Data Release | 6 | 6 | — |
| Distribution | 6 | 0 | All pending (post-manuscript) |
| **Total** | **51** | **42** | **9 remaining** |

**Status:** Manuscript, code, and data deliverables complete. Remaining items: human spot-check (10%), inter-rater agreement (needs external reviewers), repo cleanup, and distribution steps (GitHub public, Zenodo, HuggingFace, arXiv, journal submission). These require human decisions (author names, repo URLs, external review).
