# model_adjudication_labels.jsonl — provenance note

350 labels over the frozen adjudication queue, produced by a **language model**,
not by a human. Recorded here with `"source": "claude-model-adjudication"` and
`"is_human": false`.

The file as received carried `"source": "alston-adjudication"` on every row,
with a header line stating that `claude-model-adjudication` had been replaced
with `alston-adjudication`. The original provenance is restored above. Nothing
else in the rows was altered.

**These labels are not ground truth and must not be used as such.** The class-5
argument is that automated detection fails and human judgement is the reference
that demonstrates it. Scoring a model pass against a model-produced reference is
circular, and precision, recall, prevalence and kappa computed that way would
all be uninterpretable — the reliability pass in particular would measure a
generator's determinism rather than a person's consistency.

**What they legitimately are:** a second, independent detector, and a more
capable one than either the lexical or the relational detector. Structure
suggests rule application rather than case-by-case judgement — nine
`rationale_code` values, each mapping to exactly one label with no exceptions
across 350 items.

Usable, once a human reference exists, for:
- human-vs-model agreement on the same items (the interesting measurement);
- a candidate triage detector with measured precision;
- the rationale codes as a starting taxonomy of *why* items are
  under-identified: generic section header (87), key referent unspecified (65),
  gold is a navigation or link list (53), gold unrelated to question (18).

Label distribution: 231 reject, 119 keep. All 350 item IDs match the frozen
queue exactly — no extras, duplicates, or omissions.
