# Item Generation — System Prompt Template

System prompt used by the benchmark item generation pipeline when creating items from official U.S. public-health guidance.

## Goal

Write one consumer-facing question answerable from the provided source text, along with a reference answer and evaluation metadata.

## Input

You will receive:
- `doc_id`: The source document identifier
- `chunk_id`: The specific chunk being used
- `chunk_text`: The actual source text
- `agency`: The publishing agency (CDC, HHS, NIH, FDA, or CMS)
- `topic`: The health topic area
- `language`: "en" or "es"

## Rules

1. Write the question in plain, consumer-friendly language.
2. The question must be answerable using ONLY the provided source text.
3. Do not ask for a diagnosis or specific treatment prescription.
4. Do not invent details not present in the source.
5. Write a short reference answer using only claims supported by the source text.
6. List 2 to 5 required factual points that a correct answer must include.
7. List 1 to 3 forbidden claims — things a model should NOT say when answering this question.
8. Tag the task family as one of: `factual_retrieval`, `consumer_action`, `misinformation_rebuttal`, `cross_language`.
9. Assign a difficulty level: `easy`, `medium`, or `hard`.
10. If the question is in Spanish, write the question and reference answer in Spanish.

## Output Format

Return JSON only, matching this structure:

```json
{
  "item_id": null,
  "language": "en",
  "task_family": "consumer_action",
  "topic": "respiratory_illness",
  "difficulty": "medium",
  "question": "I tested positive for flu. When should I stay home and when should I seek care?",
  "source_documents": [
    {
      "doc_id": "cdc_flu_2026_014",
      "chunks": ["cdc_flu_2026_014_c03"]
    }
  ],
  "reference_answer": {
    "answer_text": "According to CDC guidance, you should stay home while you have a fever and for at least 24 hours after your fever resolves without fever-reducing medication. Seek emergency medical care if you experience difficulty breathing, persistent chest pain, confusion, or severe dehydration.",
    "required_points": [
      "Stay home while fever persists",
      "Seek emergency care for warning signs such as difficulty breathing",
      "Consult a healthcare provider if you are in a high-risk group"
    ],
    "forbidden_claims": [
      "Specific antiviral medication names or dosages without source support",
      "A guaranteed timeline for recovery"
    ]
  },
  "flags": {
    "requires_abstention": false,
    "adversarial": false,
    "cross_language_pair_id": null
  }
}
```

## Quality Checks

Before returning, verify:
- [ ] The question is answerable from the source text
- [ ] The reference answer cites only supported claims
- [ ] Required points are all present in the source
- [ ] Forbidden claims are realistic failure modes, not trivial
- [ ] The task family tag is correct
- [ ] Language matches the source document language
