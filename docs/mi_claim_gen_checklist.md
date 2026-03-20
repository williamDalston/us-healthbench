# MI-CLAIM-GEN Checklist for US-HealthBench

Based on: Gallifant et al., "The MI-CLAIM-GEN checklist for generative artificial intelligence in health," Nature Medicine, 2024.

This checklist ensures our manuscript meets the reporting standard for generative AI research in health.

---

## 1. Study Design and Problem Formulation

- [x] **1.1** Clearly state the study objective and research question
  - *Location in manuscript:* Introduction, final paragraph (5 contributions)
- [x] **1.2** Describe the health context and clinical/public-health relevance
  - *Location:* Introduction (WHO, HHS AI Strategy, language access)
- [x] **1.3** Specify the generative AI task type (e.g., text generation, summarization, question answering)
  - *Location:* Methods — System Configurations (4 system architectures)
- [x] **1.4** Justify why generative AI is being evaluated (vs. alternative approaches)
  - *Location:* Introduction (three critical gaps)

## 2. Data

- [x] **2.1** Describe the data sources with sufficient detail for reproducibility
  - *Location:* Methods — Corpus Construction (4 agencies, BFS crawling, rate limits)
- [x] **2.2** Report data selection criteria (inclusion and exclusion)
  - *Location:* Methods — Eligibility criteria (5 inclusion, 3 exclusion)
- [x] **2.3** Describe data preprocessing and transformation steps
  - *Location:* Methods — Corpus Construction (trafilatura, dedup, chunking)
- [x] **2.4** Report the dataset size, composition, and key characteristics
  - *Location:* Results — Benchmark Composition (319 docs, 1987 chunks, 2020 items)
- [x] **2.5** Discuss potential data biases and limitations
  - *Location:* Limitations (HHS missing, source freshness, 2 languages only)
- [x] **2.6** Report the languages included and any language-specific considerations
  - *Location:* Methods, Results — Multilingual Consistency (258 EN, 61 ES docs)

## 3. Model and System Description

- [x] **3.1** Identify all models used (names, versions, providers)
  - *Location:* Methods — System Configurations (heuristic-v1 baselines; LLM slots for future API runs)
- [x] **3.2** Describe system architecture(s) including any retrieval, verification, or editing components
  - *Location:* Methods — System Configurations (4-stage pipeline detailed)
- [x] **3.3** Report all prompts, instructions, and system messages used
  - *Location:* src/prompts/ (5 prompt templates), src/systems/ (system prompts in code)
- [x] **3.4** Report any fine-tuning, few-shot examples, or in-context learning used
  - *Location:* Methods (no fine-tuning; template-based generation; zero-shot baselines)
- [x] **3.5** Report inference parameters (temperature, top-p, max tokens, etc.)
  - *Location:* src/systems/*.py (temperature, max_tokens specified per system)

## 4. Evaluation

- [x] **4.1** Describe all evaluation metrics with formal definitions
  - *Location:* Methods — Scoring Rubric (5 dims × 0-2, 5 flags, GSS/MRS formulas)
- [x] **4.2** Justify the choice of metrics with respect to the health context
  - *Location:* Methods — Scoring Rubric (safety-weighted GSS), Discussion
- [x] **4.3** Describe the evaluation methodology (automated, human, or both)
  - *Location:* Methods — Human Adjudication (both: heuristic scorer + human sample)
- [ ] **4.4** For human evaluation: report number of evaluators, qualifications, training, and agreement metrics
  - *Location:* Methods — Human Adjudication (sample prepared; scoring pending)
- [x] **4.5** Report any automated evaluation tools or LLM-as-judge approaches used
  - *Location:* Methods (heuristic_scorer.py: ROUGE-L, token overlap, keyword detection)
- [x] **4.6** Report statistical methods, confidence intervals, and significance tests
  - *Location:* Methods — Statistical Analysis (bootstrap CIs, Wilcoxon signed-rank)

## 5. Results

- [x] **5.1** Report main results for all systems on all primary metrics
  - *Location:* Results — Overall System Performance (Table 1, Fig 1)
- [x] **5.2** Report results stratified by relevant subgroups (topic, language, task family)
  - *Location:* Results — Tables 2-4, topic/language/task family subsections
- [x] **5.3** Report failure modes and error analysis
  - *Location:* Results — Error Taxonomy (Fig 2, flag rate analysis)
- [x] **5.4** Report any safety-relevant findings (harmful outputs, overreach, etc.)
  - *Location:* Results — Safety and Abstention (false reassurance gradient)

## 6. Transparency and Reproducibility

- [x] **6.1** Make code publicly available
  - *Location:* Data/Code Availability Statement (GitHub, Hugging Face, Zenodo — URLs to be finalized)
- [x] **6.2** Make data/benchmarks publicly available (or describe access restrictions)
  - *Location:* Data/Code Availability Statement (benchmark, evaluation code, corpus, outputs)
- [x] **6.3** Provide sufficient detail for independent reproduction
  - *Location:* Methods (full pipeline described), docs/ (protocol, schema, rubric), src/ (all code)
- [x] **6.4** Report compute resources and costs where relevant
  - *Location:* Compute Resources section (single workstation, ~14 min, zero API cost)

## 7. Discussion and Limitations

- [x] **7.1** Discuss the implications of results for health applications
  - *Location:* Discussion — Implications for Public-Facing Health AI (3 recommendations)
- [x] **7.2** Discuss limitations of the generative AI systems evaluated
  - *Location:* Limitations — Simulated system outputs, heuristic evaluation
- [x] **7.3** Discuss limitations of the evaluation methodology
  - *Location:* Limitations — Heuristic evaluation caveat, human adjudication calibration
- [x] **7.4** Discuss potential for harm and mitigation strategies
  - *Location:* Discussion — False reassurance finding, safety editor recommendations; Ethics Statement
- [x] **7.5** Avoid overstating deployment readiness from benchmark results
  - *Location:* Limitations — Simulated outputs caveat; Conclusion — appropriately scoped claims
- [x] **7.6** Discuss equity, access, and fairness considerations
  - *Location:* Discussion — Multilingual parity finding; Data/Code Availability — responsible use note

## 8. Ethics

- [x] **8.1** Report ethical review status (IRB or equivalent)
  - *Location:* Ethics Statement — IRB exempt under 45 CFR 46.104(d)(4), public-domain data
- [x] **8.2** Report any potential conflicts of interest
  - *Location:* Competing Interests — No competing interests declared
- [x] **8.3** Discuss responsible use considerations for the released benchmark
  - *Location:* Data/Code Availability — Responsible use paragraph; Ethics Statement — adversarial content warning

---

## Completion Status

| Section | Items | Completed | Notes |
|---------|-------|-----------|-------|
| 1. Study Design | 4 | 4 | All complete |
| 2. Data | 6 | 6 | All complete |
| 3. Model/System | 5 | 5 | All complete |
| 4. Evaluation | 6 | 5 | 4.4 pending (human agreement metrics — sample ready, scoring TBD) |
| 5. Results | 4 | 4 | All complete |
| 6. Transparency | 4 | 4 | All complete (repo URLs to be finalized before submission) |
| 7. Discussion | 6 | 6 | All complete |
| 8. Ethics | 3 | 3 | All complete |
| **Total** | **38** | **37** | 1 item pending human adjudication scoring |
