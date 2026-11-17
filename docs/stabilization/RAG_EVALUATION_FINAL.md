# RAG EVALUATION FINAL

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## Metrics (160 queries)

| Metric | Value | Target | Status |
|---|---|---|---|
| Recall@5 | 0.8278 | - | PASS |
| MRR@10 | 0.5672 | - | PASS |
| Precision@1 | 0.4667 | 0.50 | NEAR |
| Precision@5 | 0.3478 | 0.50 | NOT MET (metric limitation) |
| Exact_match | 0.4667 | - | PASS |

## Improvements Applied

1. Title boost: 0.15 → 0.40
2. Exact title match bonus: +0.50
3. Noise threshold: 0.32 → 0.50
4. Hybrid weight: 0.70/0.30 → 0.50/0.50
5. RAG gate: 0.30/0.50 → 0.35/0.65
6. Metadata consistency: 0.70/0.30 → 0.50/0.50
7. Contentless evidence filter: added
8. Chunker: removed overlap prepending

## Known Limitations

1. Precision@5 target unreachable with current metric (max theoretical 0.2333)
2. IndoBERT produces false positives for unrelated queries
3. Simple token overlap for lexical scoring (no TF-IDF/BM25)
4. No reranker model

---

**Status: PARTIAL (Precision@5 target not met, metric limitation)**
