# Cover Letter — PLOS Digital Health

Dear Editors,

I submit the enclosed manuscript, "Schema Validity Is Not Semantic Validity: A Defect Taxonomy for Template-Generated Evaluation Benchmarks," for consideration as a Research Article in PLOS Digital Health.

## Why this work matters now

Health AI evaluation increasingly relies on benchmarks that are generated rather than written. Template pipelines over source corpora can produce thousands of items cheaply, and the practice is spreading faster than the validation methods applied to it. The checks in common use — schema conformance, source resolution, field completeness — were designed for human-authored items and are structurally unable to detect the failure modes that automated generation introduces.

This manuscript reports what that gap cost in a concrete, fully published case, and generalizes the result into a taxonomy others can apply.

## Contribution

I built a 2,020-item bilingual benchmark of consumer-facing U.S. public-health guidance (CDC, NIH, FDA, CMS), validated it, froze it, and content-hashed it. The validation report records 2,020 of 2,020 items passing. Auditing the frozen file afterward, I found four defect classes that the validation was incapable of seeing:

- **Template collision** — 212 question strings repeat across 664 items, and 174 of those repeats carry incompatible gold answers. One question appears 17 times with 17 unrelated correct answers. 566 items (28.0%) are unscoreable by construction.
- **Encoding corruption** — 345 items (17.1%), concentrated at 74.9% of the Spanish subset, invisible in the aggregate figure.
- **Splice contamination** — localized templates filled from another language or from page boilerplate.
- **Source pollution** — administrative pages admitted to a corpus filtered for health guidance.

The manuscript's central argument is a measurement-validity one rather than a bug report. Template collision does not behave like noise. When one question carries seventeen incompatible golds, a system answering it well fails sixteen of them, and the scoring pipeline records the generator's defect as a property of the system under test. A benchmark with unmeasured collision reports a confident measurement of the wrong thing.

## Why this submission is unusual

Benchmark defect reports are typically written by third parties auditing artifacts they did not build. This is a builder auditing his own. That has a cost in independence, which the manuscript states plainly in its limitations. It also has a benefit no third-party report can offer: the frozen artifact, the generator that produced it, the validation report that passed it, and the audit script that reproduces every reported figure are all published together, so the case can be checked rather than taken on description.

The item set is released as provisional and explicitly unfit for scoring. I am not asking the journal to accept a benchmark; I am reporting a validation failure and a detection procedure, with the artifact attached as evidence.

## Key details

- **Article type:** Research Article
- **Word count:** ~5,000 (main text)
- **Figures:** 4 (three generated from the same code path as the reported counts, so the two cannot diverge)
- **Tables:** 1 in-text; the withdrawn pre-audit analysis is retained in the release as supplementary tables, each headed with a withdrawal notice
- **Supplementary materials:** scoring rubric, pre-registered protocol (published unamended), deviations record, data-quality audit, MI-CLAIM-GEN checklist
- **Data availability:** The artifact, audit code, and documentation are public on GitHub and archived on Zenodo. The source corpus is not redistributed — the raw crawl was not retained — so the retrieval baselines are not reproducible; this is stated in the manuscript rather than left to be discovered.
- **Competing interests:** None declared.
- **Ethics:** Exclusively publicly available .gov content; no human subjects, no PII; not human subjects research under 45 CFR 46.102(e).
- **Funding:** None.

## A note on the pre-registration

The protocol was pre-registered and is published unamended, alongside a deviations document recording every point where the delivered study fell short of it — including a human-adjudication sample of 50 against a committed 250–400, with no adjudications performed. These shortfalls are disclosed rather than reconciled. Editing the protocol to match the delivery would have defeated the purpose of registering it.

## Suggested reviewers

Reviewers with expertise in: (a) benchmark design and evaluation methodology, (b) dataset quality auditing and measurement validity, or (c) multilingual NLP resource construction. Specific suggestions available on request.

I confirm that this manuscript has not been published elsewhere and is not under consideration at any other journal.

Thank you for your consideration.

Sincerely,
William Alston
Alston Analytics, LLC
will@alstonanalytics.com
