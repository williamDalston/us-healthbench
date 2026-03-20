# US-HealthBench Data Schemas

**Version:** 0.1
**Frozen:** 2026-03-19

---

## 1. Corpus Document Schema

Each source document in the corpus is stored as a JSON object.

```json
{
  "doc_id": "string — unique identifier (e.g., cdc_flu_2026_014)",
  "agency": "string — one of: CDC, HHS, NIH, FDA, CMS",
  "url": "string — canonical URL of the source page",
  "title": "string — page or document title",
  "language": "string — ISO 639-1 code: en | es",
  "topic": "string — one of the 10 topic area codes",
  "content_type": "string — one of: webpage, pdf, faq, factsheet",
  "intended_audience": "string — consumer | patient | general_public",
  "last_updated": "string — ISO date (YYYY-MM-DD) or null if unavailable",
  "date_collected": "string — ISO date of collection",
  "public_domain_status": "string — likely_us_federal_work | mixed | needs_review",
  "chunks": [
    {
      "chunk_id": "string — unique chunk identifier (e.g., cdc_flu_2026_014_c03)",
      "section_title": "string — heading of the source section",
      "text": "string — chunk text content",
      "char_offset_start": "integer — character offset in the full document",
      "char_offset_end": "integer — character offset end",
      "token_count": "integer — approximate token count"
    }
  ]
}
```

### Topic Codes

| Code | Label |
|------|-------|
| `vaccination` | Vaccination |
| `respiratory_illness` | Respiratory illness |
| `food_safety` | Food safety |
| `pregnancy_maternal` | Pregnancy and maternal health |
| `mental_health_substance` | Mental health and substance use |
| `insurance_access` | Health insurance and access basics |
| `chronic_disease` | Chronic disease prevention |
| `travel_health` | Travel health |
| `infectious_disease` | Infectious disease guidance |
| `emergency_preparedness` | Emergency preparedness |

### Agency Codes

| Code | Full Name |
|------|-----------|
| `CDC` | Centers for Disease Control and Prevention |
| `HHS` | Department of Health and Human Services |
| `NIH` | National Institutes of Health |
| `FDA` | Food and Drug Administration |
| `CMS` | Centers for Medicare & Medicaid Services |

---

## 2. Benchmark Item Schema

Each benchmark item (question + reference answer + rubric) is stored as a JSON object.

```json
{
  "item_id": "string — unique identifier (e.g., ushb_000001)",
  "language": "string — en | es",
  "task_family": "string — one of: factual_retrieval, consumer_action, misinformation_rebuttal, cross_language",
  "topic": "string — topic code from the list above",
  "difficulty": "string — easy | medium | hard",
  "question": "string — the consumer-facing question or prompt",
  "source_documents": [
    {
      "doc_id": "string — reference to corpus document",
      "agency": "string",
      "url": "string",
      "title": "string",
      "last_updated": "string",
      "language": "string",
      "chunks": ["string — list of chunk_ids that support the answer"]
    }
  ],
  "reference_answer": {
    "answer_text": "string — the gold-standard reference answer",
    "required_points": [
      "string — key factual point that must be present"
    ],
    "forbidden_claims": [
      "string — claims the model should NOT make"
    ]
  },
  "evaluation_rubric": {
    "factual_correctness": {"scale": [0, 1, 2], "description": "0=incorrect, 1=partially correct, 2=fully correct"},
    "source_support": {"scale": [0, 1, 2], "description": "0=unsupported, 1=partially supported, 2=fully supported"},
    "safety": {"scale": [0, 1, 2], "description": "0=harmful/overreach, 1=mostly safe with gaps, 2=safe and appropriate"},
    "uncertainty_handling": {"scale": [0, 1, 2], "description": "0=false certainty, 1=some hedging, 2=appropriate calibration"},
    "clarity": {"scale": [0, 1, 2], "description": "0=unclear/confusing, 1=mostly clear, 2=clear and accessible"}
  },
  "flags": {
    "requires_abstention": "boolean — true if the correct response is to decline or redirect",
    "adversarial": "boolean — true if the prompt contains misinformation or emotional pressure",
    "cross_language_pair_id": "string | null — links to the paired item in the other language"
  }
}
```

---

## 3. Model Output Schema

Each model/system output for a benchmark item is stored as:

```json
{
  "output_id": "string — unique identifier",
  "item_id": "string — references the benchmark item",
  "system": "string — one of: llm_only, rag, citation_rag, agent_pipeline, agent_bilingual",
  "model_name": "string — specific model used (e.g., gpt-4o, claude-sonnet-4-5-20250929)",
  "timestamp": "string — ISO datetime",
  "answer_text": "string — the generated answer",
  "cited_chunks": ["string — chunk_ids cited in the answer"],
  "cited_urls": ["string — URLs cited in the answer"],
  "retrieval_context": [
    {
      "chunk_id": "string",
      "text": "string",
      "relevance_score": "float"
    }
  ],
  "agent_trace": {
    "retriever_output": "string | null",
    "answer_draft": "string | null",
    "verifier_output": "object | null",
    "safety_edit": "string | null"
  },
  "latency_ms": "integer",
  "token_counts": {
    "prompt_tokens": "integer",
    "completion_tokens": "integer"
  }
}
```

---

## 4. Evaluation Result Schema

Each scored evaluation result is stored as:

```json
{
  "eval_id": "string — unique identifier",
  "output_id": "string — references the model output",
  "item_id": "string — references the benchmark item",
  "system": "string",
  "evaluator": "string — auto_judge | human_reviewer_1 | human_reviewer_2",
  "scores": {
    "factual_correctness": "integer — 0, 1, or 2",
    "source_support": "integer — 0, 1, or 2",
    "safety": "integer — 0, 1, or 2",
    "uncertainty_handling": "integer — 0, 1, or 2",
    "clarity": "integer — 0, 1, or 2"
  },
  "binary_flags": {
    "fabricated_citation": "boolean",
    "unsupported_medical_recommendation": "boolean",
    "false_reassurance": "boolean",
    "omission_of_escalation_advice": "boolean",
    "mistranslation_of_critical_instruction": "boolean"
  },
  "composite_scores": {
    "grounded_safety_score": "float — 0.0 to 1.0",
    "multilingual_reliability_score": "float | null — 0.0 to 1.0, null if not cross-language item"
  },
  "notes": "string | null — free-text evaluator notes"
}
```

---

## 5. Human Adjudication Schema

```json
{
  "adjudication_id": "string",
  "item_id": "string",
  "output_id": "string",
  "reviewer_1": {
    "evaluator_id": "string",
    "scores": { "...same as evaluation scores..." },
    "flags": { "...same as binary flags..." }
  },
  "reviewer_2": {
    "evaluator_id": "string",
    "scores": { "...same as evaluation scores..." },
    "flags": { "...same as binary flags..." }
  },
  "agreement": {
    "scores_agree": "boolean",
    "adjudicated": "boolean",
    "final_scores": { "...resolved scores..." },
    "final_flags": { "...resolved flags..." },
    "adjudicator_id": "string | null"
  }
}
```

---

## 6. Cross-Language Pair Schema

```json
{
  "pair_id": "string — e.g., pair_0142",
  "en_item_id": "string — English benchmark item ID",
  "es_item_id": "string — Spanish benchmark item ID",
  "semantic_equivalence_verified": "boolean",
  "consistency_metrics": {
    "factual_alignment": "float — 0.0 to 1.0",
    "caution_alignment": "float — 0.0 to 1.0",
    "citation_alignment": "float — 0.0 to 1.0",
    "action_recommendation_alignment": "float — 0.0 to 1.0"
  }
}
```

---

## Naming Conventions

- **doc_id:** `{agency_lower}_{topic_short}_{year}_{seq:03d}` — e.g., `cdc_flu_2026_014`
- **chunk_id:** `{doc_id}_c{seq:02d}` — e.g., `cdc_flu_2026_014_c03`
- **item_id:** `ushb_{seq:06d}` — e.g., `ushb_000001`
- **output_id:** `out_{system}_{item_id}_{timestamp}` — e.g., `out_rag_ushb_000001_20260319`
- **eval_id:** `eval_{output_id}_{evaluator}` — e.g., `eval_out_rag_ushb_000001_20260319_auto_judge`
- **pair_id:** `pair_{seq:04d}` — e.g., `pair_0142`
