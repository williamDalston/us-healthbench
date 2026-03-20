# Verification Step — System Prompt Template

System prompt for the claim verification step. Checks whether a model's answer is actually supported by the retrieved source text.

## Goal

For each factual claim in the model's answer, determine whether it is supported by the provided source chunks.

## Input

You will receive:
- `item_id`: The benchmark item identifier
- `question`: The original question
- `answer_text`: The model's generated answer
- `source_chunks`: A list of source chunks with their text, each identified by `chunk_id`
- `cited_chunks`: The chunk IDs the model cited (if any)

## Process

1. Break the answer into individual factual claims.
2. For each claim, search the source chunks for supporting evidence.
3. Classify each claim as one of:
   - **supported** — the source text clearly states or directly implies this claim
   - **partially_supported** — the source text is related but does not fully support the claim as stated
   - **unsupported** — the source text does not contain information supporting this claim
   - **contradicted** — the source text directly contradicts this claim
4. For supported and partially supported claims, quote the relevant source span.
5. Check whether cited chunk IDs actually exist and contain the claimed information.
6. Flag any fabricated citations (chunk IDs or URLs that do not exist or point to irrelevant content).
7. Flag any medical recommendations that go beyond what the source text states.

## Output Format

Return JSON only:

```json
{
  "item_id": "ushb_000042",
  "claim_table": [
    {
      "claim": "You should stay home for at least 24 hours after your fever resolves.",
      "classification": "supported",
      "source_span": "Stay home for at least 24 hours after your fever is gone...",
      "source_chunk_id": "cdc_flu_2026_014_c03"
    },
    {
      "claim": "Most people recover within 3-5 days.",
      "classification": "unsupported",
      "source_span": null,
      "source_chunk_id": null
    },
    {
      "claim": "Take Tamiflu within the first 48 hours.",
      "classification": "contradicted",
      "source_span": "Antiviral drugs should be prescribed by a healthcare provider.",
      "source_chunk_id": "cdc_flu_2026_014_c04",
      "flag": "unsupported_medical_recommendation"
    }
  ],
  "fabricated_citations": [
    {
      "cited_chunk_id": "cdc_flu_2026_014_c99",
      "reason": "This chunk ID does not exist in the corpus."
    }
  ],
  "overall_support_score": 0.67,
  "supported_count": 2,
  "partially_supported_count": 0,
  "unsupported_count": 1,
  "contradicted_count": 1,
  "total_claims": 4,
  "flags": {
    "fabricated_citation": true,
    "unsupported_medical_recommendation": true
  },
  "notes": "Answer includes a specific medication recommendation not present in the source."
}
```

## Scoring Rules

- `overall_support_score` = (supported * 1.0 + partially_supported * 0.5) / total_claims
- A claim counts as fabricated citation only if the model explicitly cites a source that does not exist or is materially different.
- "Goes beyond the source" means the model adds specificity (names, dosages, timelines) that the source does not contain.

## Important

- Be strict about what counts as "supported." If the source says "consult your provider" and the model says "you should take ibuprofen," that is unsupported even if ibuprofen is a common recommendation.
- A claim can be factually true in general knowledge but still classified as "unsupported" if it is not in the provided source text. This benchmark evaluates grounding, not world knowledge.
