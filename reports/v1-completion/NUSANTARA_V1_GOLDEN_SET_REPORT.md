# NUSANTARA V1 GOLDEN SET REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 5 — Golden Set & Evaluation
**Date:** 2026-11-12
**Branch:** codex/fullroot-control-20261007

---

## 1. Golden Set Inventory

- Total golden set files: 64 (in output/)
- Naming: {document_id}_golden_set.json
- Format: JSON with Tier A (5 questions), Tier B (2 questions), Tier C (1 question)

## 2. Current Golden Set Structure

Each golden set contains:
- `sop_id`: document ID
- `title`: document title
- `tier_a`: 5 questions (requirements, procedure, time, cost, legal)
- `tier_b`: 2 questions (typo, special case)
- `tier_c`: 1 question (out of scope)

Total: 8 questions per SOP × 64 SOPs = 512 questions

## 3. Gaps Identified

1. **No Document ID / Version ID binding**: Golden sets use document_id as sop_id but don't include version_id
2. **No expected citations**: Questions don't specify expected page numbers
3. **Generic answers**: Answers are placeholders ("Lihat bagian E persyaratan") not actual SOP content
4. **No ground truth**: No reference answer text from the SOP
5. **No evaluation results**: No automated test results recorded
6. **No no-answer questions**: Only out-of-scope, no "not available in SOP" questions
7. **No multi-step questions**: No questions requiring multiple documents

## 4. Enhancement Plan

### Enhanced Golden Set Schema
```json
{
  "sop_id": "document_id",
  "version_id": "source version hash",
  "title": "SOP title",
  "document_id": "DOC-SHA256-...",
  "questions": [
    {
      "id": "G-01",
      "query": "Apa persyaratan X?",
      "type": "requirements",
      "expected_answer": "actual answer from SOP text",
      "expected_citation_pages": [1, 2],
      "ground_truth": "verbatim text from SOP",
      "evaluation": {
        "recall": null,
        "precision": null,
        "grounded": null,
        "abstention": null
      }
    }
  ]
}
```

### Question Types Needed
- Normal: requirements, procedure, time, cost, legal
- Ambiguous: typo, abbreviation, informal language
- Multi-step: questions requiring multiple SOP sections
- Out-of-scope: unrelated queries
- No-answer: questions where SOP doesn't contain the answer

## 5. Existing Evaluation Infrastructure

- `scripts/run_search_eval.py`: Search evaluation (Recall@5, MRR@10, Precision@5)
- `scripts/evaluate_sop_golden_gate.py`: Golden gate evaluation
- Dataset: `reports/search_eval_dataset.json` (30 queries)
- Report: `reports/search_eval_report.json`

## 6. Recommendations

1. Enhance golden set generator to include version_id, citations, ground truth
2. Create 100+ representative queries across all 32 Aktif SOPs
3. Add automated regression test that runs golden sets against search
4. Include abstention verification (out-of-scope and no-answer queries)
5. Record evaluation results per SOP

## 7. Status

- Golden sets exist for all 64 documents (template level)
- Enhancement needed: version binding, citations, ground truth, evaluation results
- Automated regression not yet implemented
- Search eval: 30 queries, Recall@5=0.7444, P@5=0.2983

## 8. Commit

- Phase 5 report only, no code changes
- Golden set files in output/ (not tracked in git)
