# Under-Identification: A Benchmark Defect Class That Automated Validation Cannot Catch

**Status:** skeleton. Sections marked `[NUMBERS]` are blocked on the adjudication
labels; everything else is written from work already done. Predecessor:
*Schema Validity Is Not Semantic Validity* (DOI 10.5281/zenodo.22086136).

**Target:** short paper / preprint. The prevalence audit is a section here, not
the paper — the contribution is the class and its undetectability.

---

## 1. Introduction

Claim: generated benchmarks are validated by automated conformance checks, and
there exists at least one defect class those checks cannot reach *in principle*,
not merely in practice.

Setup, one paragraph each:
- Template-generated benchmarks are now routine; validation is schema + source.
- Prior work (the predecessor paper) named four defect classes that pass schema
  validation but are each decidable from the record or the record set by code.
- This paper names a fifth that is not, and reports what happened when two
  detectors were built for it.

Contribution list:
1. **Under-identification** defined: a question too generic to pick out its own
   gold answer.
2. Why collision detection is structurally blind to it.
3. Three detectors — lexical, relational, and model-based — each characterized
   against human labels rather than trusted or tuned away.
4. `[NUMBERS]` Human adjudication: precision, recall, stratified prevalence,
   and intra-rater agreement.
5. The implication: automated validation has a ceiling, and reporting where
   that ceiling sits is part of releasing a benchmark.

## 2. Definition

An item is **under-identified** when a competent reader, given only the
question, could not have produced its gold answer.

Worked examples (both from the released artifact):
- *"What are the key facts about symptoms and stages?"* -> gold is Lyme disease
  staging. Nothing in the question selects Lyme.
- *"What steps should I take regarding health insurance coverage and Medicare?"*
  -> gold concerns section 1915(c) HCBS waivers during emergencies.
- *"How can I protect myself and my family when it comes to summary of recent
  changes?"* -> a page section-title spliced into a question frame.

Distinguish explicitly from neighbours:
- **not** template collision: nothing is duplicated; each question is unique.
- **not** an ambiguous question: the gold is specific and determinate; the
  *question* fails to reach it.
- **not** an adversarial item: those legitimately share little vocabulary with
  their safety-refusal golds, and are exempted throughout.

## 3. Why conformance checking cannot see it

Each of the four prior classes is decidable:
| Class | Decidable from | Predicate |
|---|---|---|
| Encoding corruption | one record | mojibake signature |
| Splice artifact | one record | malformed question string |
| Template collision | the record *set* | identical question, differing gold |
| Source pollution | one record | administrative source URL |

Under-identification is decidable from neither. The record is well-formed, the
question is unique, the source is legitimate. Judging it requires modelling what
a reader could infer — a semantic judgement, not a syntactic one.

**The general form:** conformance checks answer *is this record well-formed?*
Under-identification is a property of the *relation* between question and gold,
and one that has no lexical signature. Note the asymmetry with collision, which
is also relational but decidable, because string equality is a usable proxy.

## 4. Three detectors, all characterized, none trusted

The question is not *can automation catch this?* but *how far does automation
get before a human is required?* Three detectors are reported with measured
performance against human labels; none is treated as a reference.

### 4.1 Lexical (rejected)
Flag items whose question shares little vocabulary with its gold.
33.6% of 1,058 flagged. Hand-inspection: mostly false positives — a sound item
whose gold happens to use different words is indistinguishable from a defective
one. Reported as a failed attempt, not carried forward.

### 4.2 Relational
For each question, count how many *other* items' golds match it at least as well
as its own; many rivals means the question does not select its answer. This
generalizes the collision argument from string equality to ranking.
525 of 1,058 flagged (49.6%), after exempting 202 adversarial items whose
safety-refusal golds share no vocabulary with the question by design.

### 4.3 Model
A language model applied to the same 350-item queue, one judgement per item
against the same written criterion (`model_adjudication_labels.jsonl`).
231 reject / 119 keep. Structurally it behaves as a rule applier: nine
`rationale_code` values, each mapping to exactly one label without exception
across 350 items.

**Provenance note for the paper.** These labels were received with their source
field rewritten to read as human adjudication; the original provenance was
restored before use. Worth one sentence in the methods, because the failure mode
it illustrates — model output silently becoming the reference standard — is the
same class of defect the paper is about, and it nearly happened inside the study
of it.

### 4.4 What the two automated detectors say about each other  `[PROVISIONAL]`
Detector-vs-detector agreement, pending human labels. Reported only as a
prediction to be tested, never as validation:

* The relational ranking carries signal. Model agreement with relational flags
  runs 84-88% over ranks 0-149 and falls to 52-56% over ranks 150-299.
* Recall, not precision, looks like the relational detector's real weakness: the
  model rejects 21 of 50 *unflagged* control items, and 18 of those carry
  `gold_unrelated_to_question` — a failure the relational test is blind to by
  construction, since it asks only whether rival golds match the question better.

### 4.5 On not tuning thresholds
No threshold was adjusted to make a flagged count look plausible. With no ground
truth available at the time, tuning to an expected prevalence fits the
instrument to the hypothesis. The relational detector is therefore reported as
triage-grade, not cut-grade: usable to rank, not to cut.

## 5. Human adjudication and detector evaluation  `[NUMBERS]`

Human labels are the reference. Both automated detectors are scored against
them; neither is scored against the other.

Pre-registered before any item was seen (`docs/DEVIATIONS.md`):
- Criterion fixed in writing; binary; no notes field, no revisiting.
- Blinded queue: 300 top-ranked relational flags + 50 controls drawn from
  unflagged items, shuffled, stratum never displayed. Controls are what make
  recall and prevalence estimable; precision alone would be uninterpretable.
- Model labels are withheld from the annotator during labelling. They are not
  present in the adjudication tool, which carries only question, gold, and
  required points.
- Sittings capped at 100 items against fatigue effects.
- Reliability pass: 30 items re-labelled later with prior calls hidden.

Reported per detector: precision (Wilson CI), recall, and the stratified
prevalence estimate over all 1,058 items. Reported once for the human pass:
intra-rater agreement as raw agreement and Cohen's kappa.

Precision on a ranked prefix is not prevalence. They are reported separately and
labelled as such.

**The headline quantity** is the gap between the best detector's performance and
the human reference. That number is the answer to "how far does automation get",
and it is more useful to a benchmark builder than either "automation fails" or
"automation works".

## 6. Discussion

- **How far automation gets.** `[NUMBERS]` If the model detector reaches high
  precision but poor recall, the practical guidance is that automation triages
  and a human adjudicates the residue — a workable protocol, not a counsel of
  despair.
- **A single human's labels are themselves an instrument** — hence the kappa. If
  agreement is low, the honest conclusion is that the class is hard for people
  too, which strengthens rather than weakens the undetectability claim.
- **Ceiling, not gap.** Not "our validators need improving" but "conformance
  validation has a boundary, and generated benchmarks should report where theirs
  sits."
- **Cost.** Roughly 15 seconds per item; 350 items is about 90 minutes. Cheap
  against the cost of publishing scores against items that measure nothing.
- **Generality.** The predicate is not health-specific. Any template-generated
  QA benchmark that fills a frame from a document section can produce it.

## 7. Limitations

- Single annotator, single artifact, single domain. Prevalence is an estimate
  for *this* benchmark; the class is the claim, not the rate.
- The relational detector uses bag-of-words overlap; an embedding-based version
  might do better and is untested here. Absence of a good detector is not proof
  that none exists — the argument for the ceiling is structural, and the two
  failed detectors are evidence, not proof.
- Adversarial exemption is by dataset flag; a mislabelled adversarial item would
  be silently exempted.

## 8. Data and code availability

Detector, queue builder, adjudication tool, and statistics are in the
predecessor repository. Labels released with this paper.

---

## Blocked on labels
- 4.4 becomes measured rather than provisional
- all of 5
- prevalence and recall figures wherever quoted
- the kappa in 6
