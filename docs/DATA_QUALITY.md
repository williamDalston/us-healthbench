# Data Quality Audit — v1.0 Benchmark (v0.9-provisional)

**Summary: the v1.0 item set is not fit for scoring systems as released.** It is
published as a **provisional artifact** accompanying the methodology, not as a
validated benchmark. Do not report scores against it.

Every figure below is recomputed from the frozen file by
`python -m scripts.audit_data_quality`. Re-derive rather than trust.

## Why the original validation passed

`data/benchmark_v1/validation_report.json` records 2020/2020 passing on both
schema validation and source validation. That result is accurate and also
misleading: the validator checked that each item conformed to the schema and
that its cited sources existed. It never checked whether the item's text was
correctly encoded, whether two items asking the same question agreed about the
answer, or whether a Spanish item was written in Spanish.

**Schema conformance is not semantic validity.** That is the central lesson of
this audit, and it is why the release is being restructured around the
methodology rather than the data.

## Defect classes

### 1. Encoding corruption — 345 items (17.1%)

Text was decoded as Latin-1 and re-encoded as UTF-8, producing mojibake.
Distribution is severely skewed by language:

| Language | Corrupted | Total | Share |
|---|---|---|---|
| Spanish | 215 | 287 | **74.9%** |
| English | 130 | 1,733 | 7.5% |

Example (`ushb_000004`): `¿Qué dice la guía oficial sobre â¿quã© es la obesidad??`

Three-quarters of the Spanish benchmark is affected. Bilingual evaluation is the
benchmark's principal novelty claim, and it is the most damaged part of it.

### 2. Template splice artifacts — 137 questions

Question templates were filled with unsuitable fragments, producing malformed
questions: `¿Qué dice la guía oficial sobre endoso:?` ("endorsement" — scraped
page boilerplate), `What steps should I take regarding for more help:?`

A related defect not captured by that count: some Spanish items carry an English
misinformation claim spliced into a Spanish frame, e.g. `ushb_000018` —
`Leí en internet que vaccines cause autism in children. ¿Es verdad?` These are
not valid Spanish-language items.

### 3. Duplicate questions with conflicting gold answers — 566 items (28.0%)

The 2,020 items contain only **1,568 distinct question strings**. 212 question
texts repeat across 664 items (32.9%), and **174 of those repeats carry
different gold answers**.

Worst case: *"According to FDA guidance, what should I know about health and
wellness?"* appears **17 times**, with golds covering tattoo-ink infections,
Halloween safety, salon hair straighteners, nicotine pouches, food-manufacturer
responsibility, and chemical safety — mutually exclusive answers to an identical
prompt.

**This makes the affected items unscoreable by construction.** No system can
satisfy 17 incompatible golds for one question; it will be penalized for the
item generator's template collisions rather than for its own behavior. Any
aggregate score over the full 2,020 items is therefore not a measurement of the
system under test.

### 4. Cross-language pair labels unordered — 130 of 245 pairs (53%)

In `cross_language_pairs.json`, `en_item_id` and `es_item_id` are assigned
positionally after a shuffle with no language check
(`src/benchmark/template_generator.py`). In 130 pairs the labels are reversed.
Every pair does contain exactly one English and one Spanish item, so the pairing
is sound — only the field names lie.

**Consumers must resolve language from each item's own `language` field**, which
is correct throughout. `src/run_experiment.py` has been fixed to do so; the
frozen sidecar is unchanged.

All 245 pairs additionally carry `semantic_equivalence_verified: false` — the
equivalence check the pairs depend on was never performed.

### 5. Source eligibility — 13 documents

Thirteen source documents are administrative boilerplate rather than health
guidance (privacy policies, sitemaps, contact pages), contrary to the corpus
inclusion criteria in `docs/protocol.md`. Items derived from them ask questions
like *"What are the key facts about contact us for help...?"*

## What can be salvaged

Removing defect classes 1–3 and collapsing exact duplicates leaves:

| | Items |
|---|---|
| Clean, non-conflicting, deduplicated | **1,105** (54.7%) |
| — English | 1,050 |
| — Spanish | **55** |
| — cross-language family | 55 |

This subset is not published as a benchmark. It is reported so the scale of the
recoverable material is public. Note the cost: Spanish drops from 287 items to
55, which removes the multilingual claim rather than shrinking it.

**A caution on this number.** It is clean against the *known* defect classes.
Three independent review passes over this artifact each found defect classes the
previous passes missed; the audit above is the fourth, and there is no basis for
believing it is the last. Treat 1,105 as an upper bound on recoverable items, not
a validated count.

## Consequences for the published results

The baseline results in the manuscript are computed over all 2,020 items and are
therefore affected by every defect above. They were already framed as framework
validation rather than measurements of system quality, and the heuristic
baselines were never intended to represent production performance. That framing
now carries more weight: the numbers characterize the interaction between a
keyword-based scorer and a defective item set.

The language-stratified results (Table 3) and Fig. 4 are the least interpretable,
since the Spanish side is 75% corrupted.

## Remediation

Repair requires regenerating items from source text, and the source corpus was
not retained (see `data/DATASET_CARD.md`). A corrected benchmark therefore
requires re-collection from the agency sites and a rebuilt generator that:

1. normalizes encoding at ingest and asserts round-trip integrity;
2. rejects template fills that produce malformed questions;
3. enforces question uniqueness, or requires that duplicate questions share a gold;
4. derives cross-language pairing from item language rather than position;
5. content-hashes chunk IDs instead of numbering them positionally
   (see the manuscript's "Identifier fragility" limitation);
6. applies the pre-registered pre-freeze human spot-check that was skipped
   (see `docs/DEVIATIONS.md`).

No date is committed for this work.
