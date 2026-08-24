# v1.1 Plan: from a provisional artifact to a measured result

Status: active. Owner: W. Alston. Predecessor: v1.0 defect-taxonomy release
(DOI 10.5281/zenodo.22086136), which is **frozen and not modified by this work**.

## Goal

Produce defensible evaluation numbers on a clean subset, as a **second paper**
with the v1.0 taxonomy paper as its methodological predecessor.

## Standing constraints

1. **v1.0 is immutable.** No edits to frozen items, the published manuscript, or
   the minted DOI records. All findings here land in the follow-up paper.
2. **Fix claims, never frozen data.** Carried over from v1.0.
3. **No silent negatives.** Any lookup/run failure is recorded as `unknown`,
   never as a measured zero or a genuine miss. (Learned three times: WAF sweep,
   Wayback throttle, dead overnight workflow.)
4. **Nothing scales before it is piloted.** Validate at 30 items before 1,000.
5. **Two instruments, different failure modes,** before any number is believed.

## Gate log

| Gate | Status |
|---|---|
| Clean subset extracted (1,058 items, 4 defect classes removed) | DONE |
| Human spot-check, 10% (106 items) | DONE 2026-08-24, by author |
| Condition-1 pilot (30 items x 2 systems) | pending |
| Condition-2 viability (period-correct source coverage) | BLOCKED: Wayback 429 |
| Full run | gated on all of the above |

## Known defects in *this* work (open)

| # | Defect | Status |
|---|---|---|
| D1 | Wayback sidecar queried "closest to now", not to the freeze date; 244/296 URLs falsely appeared drifted | FIXED, rebuild pending |
| D2 | Rebuild recorded HTTP 429 throttling as "not archived" | FIXED (records `unknown`) |
| D3 | Scorer floors `source_support` at 0 for any system without corpus chunk IDs; composite silently caps a no-retrieval system at 0.70 | OPEN - this is a finding, not a bug to paper over |
| D4 | Claude evaluated by a Claude-family scorer, rubric by the same author | OPEN - mitigated by comparator, disclosed in follow-up |

## Design

### Systems (>=2, so results are comparative, never a single self-scored point)

- **S1 `claude_norag`** - Claude via subscription CLI, no sources.
- **S2 `comparator_norag`** - a non-Claude model, identical prompt and pipeline.
- **S3 `claude_rag`** / **S4 `comparator_rag`** - same two, given period-correct
  source text. Conditional on the D1/D2 rebuild yielding usable coverage.

### Conditions

- **C1 no-retrieval** - runs today, needs no archive.
- **C2 with-sources** - only over items whose every cited source has a snapshot
  within 30 days of the 2026-03-20 freeze. If that subset is too small to power
  a comparison, C2 is reported as scoped or dropped, not stretched.

### Scoring

- Primary: existing heuristic scorer, four dimensions.
- **`source_support` is reported separately, never inside a cross-condition
  composite.** A composite containing a structurally floored dimension is not a
  measurement. GSS is reported for C2 only.
- Secondary: an LLM-judge pass, disagreement with the heuristic scorer reported
  rather than reconciled. Two instruments, different failure modes.

## Sequence

1. Rebuild sidecar at freeze date once the 429 clears; report real coverage. -> decides C2.
2. C1 pilot: 30 items x S1,S2. Inspect every one of the 60 outputs by hand.
3. If the pilot is clean, full C1 over 1,058 items, in overnight batches, resumable.
4. C2 pilot (30 items) only if step 1 says the subset exists.
5. Full C2 over the eligible subset.
6. Analysis, then the follow-up manuscript.

## Stop conditions

Any of these halts the run rather than being worked around: pilot outputs that
are not obviously scoreable by hand; comparator unavailable (a one-system result
is not publishable here); C2-eligible items too few for a comparison; any
instrument that reports success for work it did not do.
