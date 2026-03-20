# US-HealthBench Protocol v0.1

**Frozen:** 2026-03-19
**Status:** Draft — freeze after Day 1 review

---

## Objective

To create and evaluate a multilingual benchmark for testing whether LLM-based systems can answer consumer-facing health questions accurately, safely, and with citation-grounded support using official U.S. public-health guidance.

## Primary Research Question

Do retrieval and multi-stage verification workflows improve grounded safety and multilingual reliability compared with plain LLM answering on official U.S. public-health guidance?

## Secondary Questions

1. Does citation-constrained generation reduce unsupported claims?
2. Does multi-stage verification improve safety on adversarial prompts?
3. Is cross-language consistency meaningfully worse than same-language accuracy?
4. What are the dominant failure modes across system classes?

---

## Scope

### Languages
- English (primary)
- Spanish (paired)

### Source Agencies
- CDC (Centers for Disease Control and Prevention)
- HHS (Department of Health and Human Services)
- NIH (National Institutes of Health)
- FDA (Food and Drug Administration)
- CMS (Centers for Medicare & Medicaid Services)

### Topic Areas (8-12 domains)
1. Vaccination
2. Respiratory illness (flu, COVID-19, RSV)
3. Food safety
4. Pregnancy and maternal health
5. Mental health and substance use
6. Health insurance and access basics
7. Chronic disease prevention
8. Travel health
9. Infectious disease guidance
10. Emergency preparedness

### Task Families
1. **Fact-grounded retrieval** — questions with source-supported factual answers
2. **Consumer action prompts** — real-user "what should I do?" questions
3. **Misinformation rebuttal** — prompts containing false or slanted health claims
4. **Cross-language consistency** — semantically equivalent EN/ES question pairs

---

## Source Eligibility Criteria

### Inclusion
- Published on an official .gov domain by CDC, HHS, NIH, FDA, or CMS
- Consumer-facing or patient-facing content
- Available in English; Spanish version preferred where it exists
- Last updated within 3 years (or still posted as current guidance)
- Content type: webpage, FAQ, fact sheet, PDF guide

### Exclusion
- Internal agency memos or draft guidance
- Content primarily targeting healthcare professionals (clinical guidelines)
- Press releases or news items without substantive guidance
- Content behind authentication or paywall
- Third-party content hosted on .gov but not authored by the agency
- Content with explicit copyright restrictions (non-public-domain)

---

## Benchmark Target Size

| Component | Target |
|-----------|--------|
| Source documents | 300–600 |
| Benchmark items | 1,500–3,000 |
| Adversarial/misinfo items | ~20% of total |
| Abstention-worthy items | ~10% of total |
| Cross-language pairs | ~25% of total |

Balance across: topic, question type, language, difficulty.

---

## Data-Creation Protocol

### Step 1: Source Collection
Collect eligible pages from official agency websites using the source collector. Store raw HTML/PDF with full metadata.

### Step 2: Normalization and Deduplication
Clean HTML/PDF to plain text. Deduplicate near-duplicate pages (e.g., seasonal updates with minor changes).

### Step 3: Semantic Chunking
Chunk each source page into coherent sections (target: 150–500 tokens per chunk). Preserve section titles and hierarchy.

### Step 4: Candidate Question Generation
Use the item generation pipeline to produce candidate questions per chunk. Each item includes the question, reference answer, required points, forbidden claims, and task family tag.

### Step 5: Reference Answer Generation
Generate model answers with source-span citations. Verify each reference answer against the source chunk.

### Step 6: Verification Pass
Run the verification step to confirm every benchmark item maps to a real source span. Flag and remove items with unsupported reference answers.

### Step 7: Human Spot-Check
Human review a stratified sample (~10% of items) for quality, correctness, and clarity before freezing.

### Step 8: Freeze v1.0
Lock the benchmark. No mutations during experiments.

---

## System Configurations

### Baseline A: LLM-Only
Plain LLM with no retrieval. The model answers from parametric knowledge only.

### Baseline B: RAG
Retrieval-augmented generation. The retriever searches the official-document corpus, and the model generates an answer conditioned on retrieved chunks.

### Baseline C: RAG + Citation-Constrained
Same as B, but the model must cite specific chunk IDs or URLs for each factual claim. Claims without citations are penalized.

### Baseline D: Multi-Stage Pipeline
Four-stage pipeline:
1. **Retrieval stage** — searches the corpus
2. **Answer stage** — generates a draft answer from retrieved context
3. **Verification stage** — checks each claim against source spans
4. **Safety editing stage** — reviews for overreach, false reassurance, missing caveats

### Optional Baseline E: Bilingual Pipeline
Extends D by retrieving in the user's language when possible, falling back to English retrieval with grounded translation.

---

## Evaluation Overview

See `scoring_rubric.md` for full rubric details.

### Primary Metrics
- Answer accuracy
- Citation support rate
- Unsupported-claim rate
- Harmful overreach rate
- Appropriate abstention rate
- Completeness
- Clarity / readability
- Cross-language consistency (EN-ES)

### Composite Metrics
- **Grounded Safety Score** = f(accuracy, citation support, overreach, abstention)
- **Multilingual Reliability Score** = f(consistency, language fidelity, cross-language citation alignment)

### Human Adjudication
- Stratified sample: 250–400 answers
- Dual review with adjudication on disagreement
- Report inter-rater agreement (Cohen's kappa or Krippendorff's alpha)

---

## Statistical Analysis Plan

- Report means with 95% bootstrap confidence intervals
- Paired comparisons across workflows using appropriate tests (Wilcoxon signed-rank for non-normal distributions)
- Report effect sizes
- Stratify results by: topic, task family, language, adversarial flag
- No p-hacking: primary metrics and comparisons are frozen before experiments run

---

## Preregistration Commitments

The following are frozen on Day 1 and must not change mid-experiment:

1. Corpus inclusion/exclusion rules (above)
2. Task families (above)
3. Scoring rubric (see `scoring_rubric.md`)
4. Primary metrics (above)
5. Baseline systems (A through D above)
6. Benchmark target size (above)
7. Human-review sampling plan (above)

---

## Reporting Standard

This study follows the **MI-CLAIM-GEN** checklist for reporting generative AI in health research. See `mi_claim_gen_checklist.md` for item-by-item compliance.

---

## Ethical Considerations

- No personally identifiable information is collected or used
- All source material is official public-domain U.S. government content
- The benchmark is not a substitute for medical advice
- Generated answers are evaluated, not deployed to real users
- Adversarial prompts are designed for evaluation, not harm amplification

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-03-19 | Initial protocol draft |
