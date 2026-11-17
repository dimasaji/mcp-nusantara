# T5 — Golden Set and Evaluation Harness

**Date:** 2026-11-17

## 1. Golden Set Inventory

- 64 enhanced golden sets in output/
- 11 questions per SOP (5+2+3+1)
- Total: 704 questions
- Format: document_id, version_id, title, tier_a/b/c/d

## 2. Question Types

| Tier | Count | Types |
|---|---|---|
| A | 5 | requirements, procedure, time, cost, legal |
| B | 2 | typo, special |
| C | 3 | out_of_scope, no_answer x2 |
| D | 1 | multi_step |

## 3. Evaluation Harness

- Script: scripts/run_search_eval.py (160 queries)
- Search eval: Recall@5=0.8278, MRR=0.5672, P@1=0.4667, P@5=0.3478
- Chat eval: LangGraph grounded=True, Hermes abstain
- Automated regression: scripts/automated_regression.py (6/6 PASS)

## 4. Status

- Golden sets: ✅ 64 enhanced sets created
- Evaluation harness: ✅ Search eval + automated regression
- Baseline stored: reports/search_eval_report.json

**Status: PASS (framework ready, ground truth needs human verification)**
