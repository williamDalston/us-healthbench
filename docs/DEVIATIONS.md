# Protocol Deviations

`docs/protocol.md` pre-registers seven commitments that "must not change
mid-experiment." This document records, for the public record, every point where
the delivered study departs from them. The protocol itself is published
unamended: it states what was committed to, and this file states what happened.
Editing the protocol to match the delivery would defeat the purpose of
pre-registering it.

Status of each deviation: **disclosed**, not remediated. Remediation is the
subject of a future version (see `docs/DATA_QUALITY.md`).

---

## 1. Human-review sampling plan (commitment 7) — NOT MET

| | Pre-registered | Delivered |
|---|---|---|
| Sample size | 250–400 answers | 50 answers |
| Systems covered | not restricted | multi-stage pipeline only |
| Dual review | required | not performed |
| Inter-rater agreement | Cohen's kappa or Krippendorff's alpha, reported | not computed |

`data/experiment/human_adjudication_sample.jsonl` contains 50 records with
populated automated scores and **empty human score fields**. No human
adjudication was performed. Consequently no scorer–human agreement statistic
exists, and the heuristic scorer's validity is unverified against human
judgment.

This matters more than a sample-size shortfall normally would: the scorer is
keyword- and overlap-based, and the paper's Limitations already identify
specific ways it can be fooled (citation markers rewarded regardless of whether
they support the claim; provider-referral keywords present in all four systems
by construction). Human adjudication was the pre-registered mechanism for
calibrating exactly those biases, and it did not happen.

## 2. Cross-language pair ratio (commitment 6) — NOT MET

Pre-registered: cross-language pairs ~25% of total. Delivered: 245 pairs
covering 490 items, 12.1% of the 2,020-item benchmark — roughly half the target.

## 3. Adversarial and abstention ratios (commitment 6) — NOT MET

| Component | Target | Delivered |
|---|---|---|
| Adversarial / misinformation items | ~20% | 520 / 2,020 = 25.7% |
| Abstention-worthy items | ~10% | 120 / 2,020 = 5.9% |

Adversarial items overshoot; abstention items land at roughly half the target.
Earlier drafts of the manuscript reported the *target* figures in Methods as
though they were achieved. They now report the realized figures.

## 4. Pre-freeze human spot-check (data-creation protocol, step 7) — NOT MET

The protocol requires a human spot-check of ~10% of items (~202 items) *before*
freezing. No artifact of such a review exists in the release, and the benchmark
was frozen and content-hashed regardless. Because v1.0 is frozen, this check can
no longer be performed "before freeze" — it is superseded by the defect audit in
`docs/DATA_QUALITY.md`, which found problems a 10% spot-check would very likely
have caught before freezing.

## 5. Effect sizes (statistical analysis plan) — NOT MET

The analysis plan commits to reporting effect sizes. The manuscript reports
means, bootstrap confidence intervals, and Wilcoxon signed-rank p-values, but no
effect size for any comparison.

## 6. Agency coverage (corpus inclusion rules) — PARTIALLY MET

Five federal agencies were targeted; HHS was unreachable during collection, so
four are represented (CDC, NIH, FDA, CMS). This was disclosed in the manuscript
Limitations from the first draft.

## 7. Statistical evidence artifact — NOT SHIPPED

The abstract, Results, and Conclusion state "all pairwise p < 0.001, Wilcoxon
signed-rank." `data/experiment/experiment_stats.json` — the only released
statistics artifact — contains no p-values or test statistics; they were printed
to a console log that is not part of the release. The claim is
**reproducible from released data** (recomputing pairwise Wilcoxon on GSS from
`eval_all.jsonl` yields a largest pairwise p of 1.3e-9), but the release ships
no artifact evidencing it.

---

## Protocol status line

`docs/protocol.md` is headed "Protocol v0.1 / **Frozen:** 2026-03-19 / **Status:**
Draft — freeze after Day 1 review" — simultaneously frozen and awaiting freeze,
while `release_checklist.md` marks it finalized. The document is published as-is
rather than tidied, for the same reason as everything else in this file.
