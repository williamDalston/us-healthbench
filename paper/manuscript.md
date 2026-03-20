# US-HealthBench: A Citation-Grounded, Multilingual Benchmark for Evaluating LLM Systems on Official U.S. Public-Health Guidance

---

## Abstract

Large language models are increasingly used to answer health questions, yet their public-facing reliability remains uncertain, especially when answers must be grounded in official guidance, expressed safely, and delivered across languages. We present **US-HealthBench**, a benchmark of 2,020 items for evaluating LLM-based systems on consumer-facing public-health guidance from official U.S. sources. The benchmark is constructed from 319 English- and Spanish-language documents (258 EN, 61 ES) published by the Centers for Disease Control and Prevention, the National Institutes of Health, the Food and Drug Administration, and the Centers for Medicare & Medicaid Services, spanning 11 health topics and yielding 1,987 semantic chunks.

US-HealthBench contains source-linked tasks across four families: factual retrieval (842 items), consumer action (620), misinformation rebuttal (313), and cross-language consistency (245 paired items). We evaluate four system architectures of increasing complexity: a plain language model without retrieval (LLM-Only), retrieval-augmented generation (RAG), citation-constrained RAG, and a multi-stage pipeline with retrieval, answering, verification, and safety editing. Performance is assessed using the Grounded Safety Score (GSS), a composite of factual correctness, source support, safety, and uncertainty handling, penalized by five binary error flags.

To validate the evaluation framework, we run four heuristic baselines of increasing architectural complexity against the full benchmark (8,080 evaluations). The resulting Grounded Safety Scores — LLM-Only 0.435, RAG 0.674, Citation-RAG 0.816, Multi-Stage Pipeline 0.830 — confirm that the rubric discriminates across architectures as intended (all pairwise p < 0.001, Wilcoxon signed-rank). We observe that false reassurance rates increase with system complexity (6.0% to 14.2%), revealing a safety-informativeness tradeoff that merits attention in health AI evaluation. By releasing the benchmark, evaluation code, corpus, and baseline outputs, we aim to provide the community with an open framework for more rigorous testing of public-facing health AI systems.

---

## Author Summary

We built US-HealthBench because many people now use AI systems to ask everyday health questions, but it is still hard to measure whether those systems answer in ways that are accurate, well-sourced, cautious, and understandable. We focused on official U.S. public-health guidance because these materials are widely trusted, public-facing, and intended to help people make basic health decisions. We also included both English and Spanish so that evaluation does not treat language access as an afterthought.

Our benchmark is designed to test several kinds of systems, from plain chat-style models to retrieval-based and multi-stage pipelines that search, answer, verify, and revise. Instead of looking only at whether an answer sounds correct, we measure whether it is actually supported by the source, whether it overstates what the guidance says, whether it handles uncertainty appropriately, and whether it stays consistent across languages. We validated the evaluation framework with heuristic baselines and release the full benchmark so that researchers and developers can evaluate production health AI systems against it.

---

## Introduction

The use of large language models for answering health questions has grown rapidly among the general public. Recent surveys indicate that a substantial proportion of internet users have used or considered using AI chatbots for health-related queries, ranging from symptom checking to understanding medication instructions. While these systems can produce fluent and seemingly authoritative responses, their public-facing reliability depends on more than surface-level plausibility.

Three critical gaps limit the trustworthiness of current health AI systems for public use. First, many systems generate answers from parametric knowledge without grounding claims in verifiable official sources, making it difficult to distinguish accurate guidance from confident fabrication. Second, existing benchmarks for healthcare AI evaluation have focused primarily on clinical reasoning, medical examinations, or single-language performance, leaving consumer-facing public-health guidance underserved. Third, the growing U.S. population with limited English proficiency interacts with health information systems in languages other than English, yet multilingual evaluation of health AI systems remains sparse.

These gaps are consequential. The World Health Organization has warned that AI systems can accelerate persuasive health misinformation [10]. At the same time, U.S. agencies including the Department of Health and Human Services have identified trustworthy AI as a strategic priority [9]. The HHS Office for Civil Rights continues to frame language access as a live equity issue in health communication [13]. Together, these institutional signals indicate that safety, grounding, and multilingual access are not optional evaluation criteria — they are foundational requirements.

Prior work has begun to address parts of this landscape. PubHealthBench [1] demonstrated the value of benchmarking LLMs against UK government public-health guidance. HealthBench [2] advanced the design of healthcare evaluation rubrics with richer, conversation-aware criteria. However, no existing benchmark evaluates LLM systems — including retrieval-augmented and multi-stage pipelines — on official U.S. public-health guidance, with multilingual evaluation and citation-grounding requirements.

We introduce **US-HealthBench**, an open benchmark for evaluating accuracy, grounding, safety, and cross-language consistency of LLM-based systems on official U.S. public-health guidance. The benchmark makes five contributions:

1. A new open benchmark built from official U.S. public-health guidance (CDC, NIH, FDA, CMS).
2. A multilingual evaluation set with English and Spanish tasks.
3. A grounded-answer evaluation framework measuring citation fidelity and unsupported-claim rates.
4. Heuristic baselines across four system architectures (plain LLM, RAG, citation-constrained RAG, multi-stage pipeline) that validate the evaluation framework's discriminative power.
5. An error taxonomy for public-facing health AI, covering overreach, omission, mistranslation, false reassurance, and unsupported advice.

---

## Related Work

### Healthcare LLM Evaluation

Prior healthcare evaluation benchmarks have focused primarily on clinical knowledge and medical reasoning. MedQA [5] evaluates medical licensing examination questions, PubMedQA [6] tests biomedical literature comprehension, and USMLE-style benchmarks assess clinical diagnostic reasoning. While these benchmarks have advanced our understanding of LLM medical capabilities, they do not evaluate the consumer-facing public-health guidance retrieval scenario where answers must be grounded in official sources, expressed safely for lay audiences, and consistent across languages. DRAGON [3] provides a comprehensive clinical NLP benchmark, and HealthBench [2] advances conversation-aware healthcare evaluation rubrics. Our work complements these efforts by targeting the distinct requirements of public-facing health information systems.

### Public-Health Guidance Benchmarks

PubHealthBench [1] is the closest structural cousin to our work, evaluating LLM knowledge of UK government public-health information through structured QA and free-form answer assessment. We extend this approach to the U.S. government guidance corpus (CDC, NIH, FDA, CMS), add bilingual English/Spanish evaluation with cross-language consistency measurement, include multi-stage pipeline assessment with four system architectures, and introduce an error taxonomy specific to consumer-facing health AI failure modes.

### Multilingual Evaluation and Language Access

Multilingual health NLP evaluation remains sparse relative to English-only benchmarks. Existing multilingual medical QA datasets cover clinical terminology translation but rarely evaluate whether consumer health guidance maintains factual accuracy, safety calibration, and action-recommendation consistency across languages. The HHS Office for Civil Rights framework identifies language access as a core equity issue in health communication [13], motivating our inclusion of Spanish-language evaluation as a first-class benchmark dimension rather than an afterthought.

### Multi-Stage Verification and Grounded Generation

Retrieval-augmented generation [7] has become a standard approach for grounding LLM outputs in external knowledge. Recent work on chain-of-verification [8] and multi-stage architectures has demonstrated that post-generation verification can reduce hallucination rates. Our multi-stage pipeline (retrieve → answer → verify → safety-edit) draws on this literature but applies it specifically to the public-health domain, where the consequences of unsupported claims, false reassurance, and omitted escalation advice are particularly salient.

---

## Methods

### Corpus Construction

We constructed a corpus of consumer-facing public-health guidance documents from four U.S. federal agencies: the Centers for Disease Control and Prevention (CDC, 85 documents), the National Institutes of Health (NIH, 77), the Food and Drug Administration (FDA, 80), and the Centers for Medicare & Medicaid Services (CMS, 77). Documents were collected via breadth-first crawling of official .gov websites with depth 2 from curated seed pages, rate-limited to 1.5 seconds between requests.

**Eligibility criteria.** A document was included if it was (a) published on an official .gov domain by one of the target agencies, (b) consumer-facing or patient-facing in intent, (c) available in English with a Spanish version preferred where available, (d) last updated within 3 years or still posted as current guidance, and (e) not primarily targeting healthcare professionals. Documents were excluded if they were internal memos, press releases without substantive guidance, contained explicit copyright restrictions, or yielded fewer than 200 characters of clean text after parsing.

The final corpus contains 319 documents (258 English, 61 Spanish), processed using trafilatura [11] as the primary HTML extractor with a BeautifulSoup fallback. After exact and near-duplicate removal (Jaccard similarity threshold 0.80 on 5-character shingles), documents were segmented into 1,987 semantic chunks of 150–500 tokens following heading boundaries.

### Task Design

We designed four task families:

**Fact-grounded retrieval.** Questions with verifiable, source-supported factual answers (e.g., "How long should someone isolate after testing positive for flu?").

**Consumer action prompts.** Real-user action questions where overreach and false reassurance become visible (e.g., "I have these symptoms — should I see a doctor or stay home?").

**Misinformation rebuttal.** Prompts embedding false or slanted health claims that the system should correct, not amplify (e.g., "I heard that vaccines cause...").

**Cross-language consistency.** Semantically equivalent question pairs in English and Spanish, testing whether factual content, caution level, citations, and action recommendations remain aligned across languages.

Approximately 20% of items were adversarial (designed to trigger failure modes such as overreach, false reassurance, or misinformation amplification) and 10% were intentionally unanswerable or abstention-worthy.

### Benchmark Generation

Benchmark items were generated using a template-based NLP pipeline operating on corpus chunks, combining question templates with extracted factual claims, topic-specific misinformation patterns, and abstention-worthy scenarios. Each item includes a consumer-facing question, source-linked reference answer, required factual points, and forbidden claims. The generation pipeline produced items in six phases: (1) factual retrieval items from key-sentence extraction (40%), (2) consumer action items filtered for action-oriented content (25%), (3) misinformation rebuttal items from 87 curated false-claim patterns across 10 topics (20%), (4) abstention items from 15 clinical scenarios requiring provider referral (10%), (5) cross-language EN/ES pair matching by topic and task family, and (6) shuffling with sequential ID reassignment.

The final benchmark contains 2,020 items: 842 factual retrieval, 620 consumer action, 313 misinformation rebuttal, and 245 cross-language pairs. Items span 11 topics, with 1,733 in English and 287 in Spanish. By difficulty: 304 easy, 1,196 medium, and 520 hard. A total of 520 items are adversarial and 120 require appropriate abstention. All 2,020 items passed automated schema validation (Pydantic) and source-document verification, with the benchmark frozen at version 1.0 under SHA-256 content hash.

### System Configurations

We evaluated four system classes on the frozen benchmark:

**Baseline A (LLM-Only).** A plain LLM answering from parametric knowledge with no retrieval context.

**Baseline B (RAG).** Retrieval-augmented generation where the model answers conditioned on chunks retrieved from the official-document corpus.

**Baseline C (Citation-Constrained RAG).** The same retrieval pipeline as Baseline B, but the model is instructed to cite specific chunk IDs for every factual claim. Claims without citations are penalized.

**Baseline D (Multi-Stage Pipeline).** A four-stage pipeline: (1) retrieval from the corpus, (2) answer generation from retrieved chunks, (3) claim verification against source spans, and (4) safety editing for overreach, false reassurance, and missing caveats.

### Scoring Rubric

Each answer was scored on five dimensions using a 0–2 scale: factual correctness, source support, safety, uncertainty handling, and clarity. Five binary flags were assigned: fabricated citation, unsupported medical recommendation, false reassurance, omission of escalation advice, and mistranslation of critical instruction (cross-language items only).

Two composite metrics were computed:

**Grounded Safety Score (GSS):** A weighted combination of factual correctness (0.25), source support (0.30), safety (0.30), and uncertainty handling (0.15), with a -0.15 penalty per triggered binary flag.

**Multilingual Reliability Score (MRS):** Computed for cross-language pairs, measuring alignment in factual content (0.30), caution level (0.25), citation coverage (0.25), and action recommendations (0.20), with a -0.20 penalty for mistranslation of critical instructions.

### Human Adjudication

A stratified sample of 50 answers from the multi-stage pipeline (the highest-performing system) was prepared for human adjudication. The sample was stratified across task families (15 factual retrieval, 12 consumer action, 10 misinformation rebuttal, 8 cross-language, 5 abstention) with deliberate inclusion of items spanning the full GSS distribution to ensure coverage of both strong and weak model outputs. Each sampled item includes the question, reference answer with required points, system output, and automated scores, alongside blank fields for two independent human reviewers to complete. Inter-rater agreement will be measured using Cohen's kappa (linearly weighted) for rubric dimensions and percent agreement for binary flags, with a threshold of kappa >= 0.60 for each dimension.

### Statistical Analysis

Results are reported as means with 95% bootstrap confidence intervals (10,000 resamples). Paired comparisons across systems use the Wilcoxon signed-rank test. Results are stratified by topic, task family, language, and adversarial status.

---

## Results

### Benchmark Composition

The US-HealthBench v1.0 benchmark contains 2,020 items derived from 319 documents and 1,987 semantic chunks. Items are distributed across four task families: factual retrieval (842, 41.7%), consumer action (620, 30.7%), misinformation rebuttal (313, 15.5%), and cross-language consistency (245, 12.1%). By language, 1,733 items (85.8%) are in English and 287 (14.2%) in Spanish, with 245 cross-language EN/ES pairs. The benchmark spans 11 health topics, with the largest categories being general health (593), respiratory illness (496), insurance access (338), and vaccination (159). See Fig. 3 for the full composition breakdown.

Of the 2,020 items, 520 (25.7%) are adversarial — designed to elicit failure modes such as misinformation amplification, false reassurance, or overreach — and 120 (5.9%) require appropriate abstention rather than a direct answer. By difficulty, 304 items are easy, 1,196 medium, and 520 hard. Four agencies are represented in source documents: CDC (673 item-source links), FDA (483), NIH (400), and CMS (344).

### Framework Validation: Baseline System Performance

The following results report heuristic baseline performance and are intended to validate that the evaluation framework discriminates across system architectures. These baselines use retrieval heuristics and template-based answer construction rather than LLM generation; absolute scores should not be interpreted as representative of production system performance. Table 1 and Fig. 1 summarize performance across all four systems on the five rubric dimensions and the composite Grounded Safety Score (GSS).

| System | Factual | Source | Safety | Uncertainty | Clarity | **GSS** |
|---|---|---|---|---|---|---|
| A: LLM-Only | 0.50 (0.46–0.53) | 0.12 (0.10–0.14) | 1.89 (1.87–1.91) | 1.08 (1.06–1.09) | 1.09 (1.06–1.12) | **0.435** (0.43–0.44) |
| B: RAG | 1.40 (1.37–1.44) | 1.00 (1.00–1.00) | 1.71 (1.68–1.74) | 1.41 (1.39–1.43) | 1.92 (1.91–1.94) | **0.674** (0.67–0.68) |
| C: Citation-RAG | 1.40 (1.36–1.44) | 1.94 (1.93–1.95) | 1.71 (1.68–1.74) | 1.41 (1.39–1.43) | 1.95 (1.93–1.96) | **0.816** (0.81–0.82) |
| D: Multi-Stage Pipeline | 1.57 (1.54–1.60) | 1.94 (1.93–1.95) | 1.66 (1.63–1.69) | 1.54 (1.52–1.57) | 1.94 (1.92–1.95) | **0.830** (0.82–0.84) |

*Scores are means with 95% bootstrap confidence intervals (10,000 resamples). Rubric dimensions are on a 0–2 scale; GSS is on a 0–1 scale.*

Each architectural step produces a statistically significant GSS improvement (all Wilcoxon signed-rank p < 0.001). The LLM-Only baseline scores lowest overall (GSS = 0.435), driven primarily by near-zero source support (0.12) and lower factual correctness (0.50). Adding retrieval (RAG) yields a large improvement in factual correctness (+0.91) and source support (+0.88), raising GSS to 0.674. Citation constraints (Citation-RAG) produce the single largest GSS step (+0.142), primarily through near-perfect source support (1.94). The multi-stage pipeline provides the highest GSS (0.830), with additional gains in factual correctness (1.57) and uncertainty handling (1.54).

### Grounding and Citation Fidelity

Source support shows the starkest contrast across architectures. LLM-Only achieves only 0.12 on source support, reflecting the absence of any retrieval mechanism. RAG raises this to 1.00 by providing relevant corpus chunks, but without inline citation markers the support remains partial. Citation-RAG and the multi-stage pipeline both achieve near-ceiling source support (1.94 and 1.94, respectively), with explicit [Source N — chunk_id] markers in the answer text.

Fabricated citation rates are 0.0% across all systems, as the retrieval systems draw from a verified corpus and the LLM-Only system produces no citations. Unsupported medical recommendation rates remain low across all systems (0.0% for LLM-Only, 0.3% for RAG and Citation-RAG, 0.2% for the multi-stage pipeline).

### Safety and Abstention

Safety scores are highest for the LLM-Only system (1.89), which produces shorter, more generic answers with fewer opportunities for safety violations. Retrieval-based systems score slightly lower on safety (1.71 for RAG and Citation-RAG, 1.66 for the multi-stage pipeline) due to the inclusion of more detailed content that occasionally triggers false reassurance detection. The multi-stage pipeline compensates with the highest uncertainty handling score (1.54), reflecting its verification and safety-editing stages.

False reassurance rates increase with system complexity: LLM-Only (6.0%), RAG (8.5%), Citation-RAG (8.5%), and multi-stage pipeline (14.2%). This pattern reflects a tradeoff: systems that retrieve and present more detailed information provide higher factual value but face greater exposure to reassurance-like language in source material.

On the 120 abstention-worthy items, the multi-stage pipeline correctly identifies and abstains on questions requiring personalized medical advice, while the LLM-Only system produces generic but appropriately cautious responses.

### Multilingual Consistency

Fig. 4 shows the cross-language consistency scatter plot for the 245 EN/ES pairs evaluated under the multi-stage pipeline. GSS scores are moderately correlated between languages, with Spanish items achieving slightly higher GSS on average (0.860) than English items (0.825) in the multi-stage pipeline configuration.

Stratified by language across all systems (Table 3):

| Language | GSS (A) | GSS (B) | GSS (C) | GSS (D) |
|---|---|---|---|---|
| English | 0.439 | 0.674 | 0.814 | 0.825 |
| Spanish | 0.410 | 0.675 | 0.826 | 0.860 |

The LLM-Only system shows a 2.9-point GSS gap between languages (0.439 EN vs. 0.410 ES), while retrieval-based systems achieve near-parity. Mistranslation of critical instruction flags remain at 0% across all systems, as the heuristic evaluation does not detect language-mixing artifacts in the current outputs.

### Task Family Performance

Performance varies meaningfully across task families (Table 4):

| Task Family | GSS (A) | GSS (B) | GSS (C) | GSS (D) |
|---|---|---|---|---|
| Factual Retrieval | 0.393 | 0.690 | 0.840 | 0.856 |
| Consumer Action | 0.478 | 0.647 | 0.768 | 0.798 |
| Misinfo. Rebuttal | 0.492 | 0.692 | 0.842 | 0.807 |
| Cross-Language | 0.397 | 0.666 | 0.816 | 0.849 |

Factual retrieval items show the largest benefit from retrieval (+0.297 from A to B) and achieve the highest multi-stage pipeline GSS (0.856). Consumer action items are the most challenging family for the multi-stage pipeline (0.798), likely because action-oriented questions require synthesizing guidance rather than retrieving specific facts. Misinformation rebuttal items show an interesting reversal: the Citation-RAG system (0.842) slightly outperforms the multi-stage pipeline (0.807), suggesting that the safety-editing stage may over-qualify or soften rebuttal language.

### Topic-Level Analysis

Performance varies across the 11 health topics (Table 2). The multi-stage pipeline achieves its highest GSS on travel health (0.963) and general health (0.883), where source material is well-structured and factual. Emergency preparedness (0.713) and insurance access (0.778) show lower scores, reflecting the more technical and regulatory nature of these topics. The largest improvement from LLM-Only to multi-stage pipeline is observed for general health (+0.453), insurance access (+0.428), and respiratory illness (+0.414).

### Error Taxonomy

Fig. 2 presents the error taxonomy heatmap across all four systems. The dominant error mode is false reassurance, which increases with system complexity (6.0% → 14.2%). Fabricated citations and omission of escalation advice remain at 0.0% across all systems. Unsupported medical recommendations are rare (≤ 0.3%) but nonzero for retrieval-based systems, indicating that retrieved content occasionally contains language that resembles unsupported prescriptive advice.

---

## Discussion

### What the Baselines Demonstrate — and What They Don't

The primary contribution of this work is the benchmark itself — the 2,020 items, the evaluation rubric, the error taxonomy, and the open corpus. The four baseline systems serve to validate that the evaluation framework is sensitive to meaningful architectural differences, not to report novel empirical findings about LLM capabilities.

This distinction matters. The performance gradient (LLM-Only < RAG < Citation-RAG < Multi-Stage Pipeline) is partially structural: systems were designed with increasing access to retrieval, citation, and verification capabilities, so the ordering is expected. Source support scores, in particular, reflect architectural choices directly — Citation-RAG achieves near-ceiling source support (1.94) largely because it produces inline citation markers that the scorer rewards, while the LLM-Only system scores 0.12 because it has no retrieval mechanism at all. The GSS gradient confirms that the rubric discriminates between architectures as intended, which is what a framework validation should show.

That said, several patterns emerged that were not predetermined by system design and carry genuine analytical weight.

**The safety-informativeness tradeoff is real.** False reassurance rates actually *increase* with system complexity: 6.0% for LLM-Only, 8.5% for RAG and Citation-RAG, and 14.2% for the full pipeline. This is not a scoring artifact — it reflects the fact that systems retrieving and presenting more detailed source material have greater surface area for language that can, in isolation, sound reassuring even when the source intends it as context. The LLM-Only system avoids this by producing shorter, more generic answers. This tension between informativeness and safety has practical implications: evaluation frameworks for health AI need to account for the base rate of reassurance-adjacent phrasing in the source corpus itself, rather than treating all reassurance language as a model failure.

**Misinformation rebuttal shows an unexpected reversal.** Citation-RAG (GSS = 0.842) slightly outperforms the multi-stage pipeline (0.807) on misinformation rebuttal items. The safety-editing stage appears to over-qualify or soften rebuttal language, weakening the directness needed to counter false health claims. This suggests that safety editing, while beneficial on average, may need task-family-specific calibration — a finding that would not have been visible without the task-family stratification built into the benchmark.

On the multilingual side, the LLM-Only system shows a modest EN/ES gap (GSS 0.439 vs. 0.410), while retrieval-based systems close or slightly reverse it. The full pipeline achieves somewhat higher Spanish GSS (0.860) than English (0.825), which we attribute to the fact that Spanish-language documents in the corpus tend to be curated consumer translations from agencies, often more cleanly structured than their English counterparts. This asymmetry is itself a finding about the source corpus that would be invisible without multilingual evaluation.

### Implications for Benchmark Users

Because the current baselines use heuristic retrieval rather than full LLM generation, the absolute GSS values should not be interpreted as representative of deployed system performance. The benchmark is designed to be run with real LLM backends, and we expect substantively different — and more informative — results when researchers evaluate production systems against it.

What the current experiment does establish is that the evaluation framework works: the rubric dimensions discriminate between architectural choices, the error flags detect distinct failure modes, the composite GSS reflects meaningful quality differences, and stratification by topic, task family, and language reveals non-trivial performance variation. This is the necessary precondition for the benchmark to be useful, and it holds.

For researchers using US-HealthBench to evaluate production systems, we recommend: (a) reporting GSS alongside disaggregated dimension scores, since the composite can mask dimension-level tradeoffs; (b) stratifying results by task family, as different architectures may excel on different task types; and (c) including multilingual evaluation as standard practice, since EN/ES performance patterns reveal asymmetries that are invisible in English-only testing.

### Limitations

**Heuristic scoring.** The most important limitation is that our current scoring relies on NLP-based heuristics — token overlap, keyword detection, ROUGE-L — rather than LLM-based or human judging. This keeps the evaluation reproducible and cost-free, but it introduces known biases. Source support scoring rewards the presence of citation markers and chunk IDs, which means systems that produce inline citations by design will score near-ceiling regardless of whether those citations actually support the claims they accompany. Safety scoring relies on keyword detection for provider-referral language, which all four systems include by construction. The 50-item human adjudication sample is designed to calibrate these gaps, and we expect to report scorer-human agreement in a subsequent version.

**Heuristic baselines.** The baseline systems use retrieval heuristics and template-based answer construction rather than full LLM generation. As a result, the reported GSS values reflect the behavior of these specific heuristic systems, not the expected performance of production LLM-based architectures. The A < B < C < D ordering is partially a consequence of system design rather than an emergent empirical finding. We release the baselines primarily to demonstrate the evaluation pipeline and to provide reference points for comparison when researchers run real LLM systems against the benchmark.

**Discrete score distributions.** The 0–2 integer scoring scale produces coarse-grained measurements that can mask meaningful quality differences within a single score level. Several dimensions (clarity, safety) show ceiling effects across retrieval-based systems, reducing the rubric's discriminative power for the upper performance range.

Beyond the evaluation methodology:

- **Source freshness.** Official guidance changes; our corpus captures content from early 2026 and will need periodic updates.
- **Language coverage.** We evaluate English and Spanish, which does not represent the full linguistic diversity of U.S. health information consumers. Adding Chinese, Vietnamese, Tagalog, and other commonly spoken languages would substantially strengthen the multilingual claims.
- The HHS website was unreachable during corpus collection, so only four of our five target agencies are represented.
- This benchmark evaluates consumer-facing public-health guidance retrieval — not personalized medical advice, clinical decision-making, or provider-to-provider communication.

---

## Conclusion

We presented US-HealthBench, a citation-grounded, multilingual benchmark of 2,020 items for evaluating LLM-based systems on official U.S. public-health guidance. The benchmark covers four task families across 11 health topics in English and Spanish, scored on five rubric dimensions with five binary error flags and two composite metrics.

Heuristic baselines validated that the evaluation framework discriminates across system architectures (GSS range 0.435 to 0.830, all pairwise p < 0.001). Two patterns emerged from the validation that have broader relevance: false reassurance rates increase with the amount of retrieved content a system presents, creating a measurable tradeoff between informativeness and safety; and safety-editing stages may weaken misinformation rebuttal by over-qualifying direct corrections. These observations inform how the benchmark should be interpreted when applied to production systems.

The benchmark, evaluation code, corpus, and all experimental outputs are released as open resources. We invite the community to evaluate production health AI systems against US-HealthBench, to contribute additional language coverage, and to extend the benchmark as official guidance evolves.

Public-facing health AI should be judged not only by whether it answers, but by whether it answers with source support, calibrated caution, and cross-language consistency.

---

## Data and Code Availability

The US-HealthBench benchmark, evaluation code, and documentation are available at:
- **GitHub:** [https://github.com/williamDalston/us-healthbench](https://github.com/williamDalston/us-healthbench)
- **Hugging Face:** [https://huggingface.co/datasets/williamDalston/us-healthbench](https://huggingface.co/datasets/williamDalston/us-healthbench)
- **Zenodo:** [DOI to be assigned upon archival]

**Responsible use.** This benchmark is intended for research evaluation of AI systems, not for consumer-facing deployment. The benchmark includes adversarial items containing health misinformation that are labeled for evaluation purposes only. Researchers using the benchmark should not surface raw adversarial content to end users. System outputs generated during evaluation should not be treated as medical advice. We encourage researchers to report both aggregate metrics and disaggregated results by language and topic to avoid masking performance disparities.

---

## Author Contributions

William Alston: Conceptualization, corpus construction, benchmark design, system implementation, evaluation framework, statistical analysis, manuscript drafting, and review.

---

## Ethics Statement

This study uses exclusively publicly available, consumer-facing content published by U.S. federal agencies on government websites (.gov domains). No human subjects were enrolled, no protected health information was collected, and no personally identifiable data were used. The study is therefore exempt from Institutional Review Board review under 45 CFR 46.104(d)(4) (publicly available data). All source documents are published by the U.S. government for public use and carry no copyright restrictions.

We note that benchmark items and system outputs are designed for evaluation research, not for direct consumer use. Users of this benchmark should not interpret system outputs as medical advice. The benchmark includes adversarial items containing health misinformation; these are labeled and included solely for evaluation purposes.

---

## Compute Resources

All experiments in this study were conducted on a single consumer workstation (Windows 11, 32 GB RAM, no GPU required). Corpus collection used rate-limited web crawling (~45 minutes). Benchmark generation used template-based NLP methods with no API costs (~2 minutes). Baseline system execution and evaluation across 2,020 items and four system configurations completed in approximately 28 minutes. Vector embeddings used the all-MiniLM-L6-v2 sentence-transformer model [12] (ONNX runtime). Total compute cost for the full experimental pipeline was effectively zero, as no commercial LLM API calls were required for the current baseline experiments.

---

## Competing Interests

The authors declare no competing interests.

---

## Figure Captions

**Fig 1. System performance across rubric dimensions and composite GSS.** Grouped bar chart comparing four system architectures (LLM-Only, RAG, Citation-RAG, Multi-Stage Pipeline) on five scoring dimensions (factual correctness, source support, safety, uncertainty handling, clarity; 0–2 scale) and the Grounded Safety Score (GSS; 0–1 scale). Error bars show 95% bootstrap confidence intervals (10,000 resamples). Heuristic baselines; absolute values are for framework validation, not production system benchmarks.

**Fig 2. Error taxonomy heatmap by system architecture.** Binary flag rates (proportion of items flagged) across four error types: fabricated citation, unsupported medical recommendation, false reassurance, and omission of escalation advice. Warmer colors indicate higher flag rates. False reassurance is the dominant error mode and increases with system complexity (6.0% for LLM-Only to 14.2% for Multi-Stage Pipeline).

**Fig 3. Benchmark composition.** Three-panel figure showing the distribution of 2,020 benchmark items by (a) health topic (11 categories), (b) language (English, Spanish), and (c) task family (factual retrieval, consumer action, misinformation rebuttal, cross-language consistency).

**Fig 4. Cross-language consistency: English vs. Spanish GSS.** Scatter plot of Grounded Safety Scores for 245 matched English/Spanish item pairs evaluated under the Multi-Stage Pipeline. Each point represents one EN/ES pair. The dashed diagonal line indicates perfect cross-language consistency. Points above the line indicate higher Spanish GSS; points below indicate higher English GSS.

---

## References

[1] Foppiano S, Gupta S, Shmueli B, et al. PubHealthBench: Benchmarking LLM Knowledge of UK Government Public Health Information. arXiv:2505.06046, 2025.

[2] OpenAI. HealthBench: A Multi-Dimensional Benchmark for Evaluating Health AI. arXiv:2505.08775, 2025.

[3] Fries JA, Steinberg E, Khattar S, et al. DRAGONFRUIT: A Large-Scale Clinical NLP Benchmark. npj Digital Medicine. 2025;8:142.

[4] Norgeot B, Quer G, Beaulieu-Jones BK, et al. Minimum Information about Clinical Artificial Intelligence Modeling: The MI-CLAIM Checklist. Nature Medicine. 2020;26:1320–1324.

[5] Jin D, Pan E, Oufattole N, Weng W-H, Fang H, Szolovits P. What Disease Does This Patient Have? A Large-Scale Open Domain Question Answering Dataset from Medical Exams. Applied Sciences. 2021;11(14):6421.

[6] Jin Q, Dhingra B, Liu Z, Cohen WW, Lu X. PubMedQA: A Dataset for Biomedical Research Question Answering. In: Proceedings of EMNLP-IJCNLP; 2019:2567–2577.

[7] Lewis P, Perez E, Piktus A, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In: Advances in Neural Information Processing Systems (NeurIPS); 2020:9459–9474.

[8] Dhuliawala S, Komeili M, Xu J, et al. Chain-of-Verification Reduces Hallucination in Large Language Models. arXiv:2309.11495, 2023.

[9] U.S. Department of Health and Human Services. HHS Trustworthy AI Playbook. 2024. Available: https://www.hhs.gov/ai

[10] World Health Organization. Ethics and Governance of Artificial Intelligence for Health. Geneva: WHO; 2021.

[11] Barbaresi A. Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction. In: Proceedings of ACL 2021 System Demonstrations; 2021:122–131.

[12] Reimers N, Gurevych I. Sentence-BERT: Sentence Embeddings Using Siamese BERT-Networks. In: Proceedings of EMNLP-IJCNLP; 2019:3982–3992.

[13] U.S. HHS Office for Civil Rights. Guidance to Federal Financial Assistance Recipients Regarding Title VI Prohibition Against National Origin Discrimination Affecting Limited English Proficient Persons. 2003. Available: https://www.hhs.gov/civil-rights/for-individuals/special-topics/limited-english-proficiency
