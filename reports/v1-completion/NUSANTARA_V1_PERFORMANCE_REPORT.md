# NUSANTARA V1 PERFORMANCE REPORT

**Contract:** NUS-V1-HYBRID-DEEPSEEK-001
**Date:** 2026-11-16
**Branch:** codex/fullroot-control-20261007

---

## 1. SOP Processing Performance

### Baseline (2 SOPs — CAPIL_04, CAPIL_02)
| Metric | Value |
|---|---|
| Total time | 132.3s |
| Avg per SOP | 66.1s |
| Breakdown | Upload (1-2s) + Docling extraction (50-80s) + indexing (5-10s) |

### Estimated for 42 SOPs
| Metric | Value |
|---|---|
| Total estimated | ~46 minutes |
| Per SOP | ~66s |

### Extraction Status Distribution (180 total extractions)
| Status | Count |
|---|---|
| COMPLETE | 83 |
| PARTIAL | 70 |
| FAILED | 27 |

### Docling Worker Performance
| Metric | Value |
|---|---|
| Avg extraction time | ~60-80s per SOP |
| Pages per SOP | 2-6 |
| Blocks per SOP | 100-500 |
| Tables per SOP | 1-3 |
| CPU threads | 1 (reduced from 2 for stability) |
| Memory per extraction | ~500 MB |

## 2. Search Performance

### From Search Eval (160 queries, API endpoint)
| Metric | Value |
|---|---|
| Recall@5 | 0.8278 |
| MRR@10 | 0.5672 |
| Precision@1 | 0.4667 |
| Precision@5 | 0.3478 |
| Exact_match | 0.4667 |
| Latency mean | 192.2 ms |
| Latency median | 178.9 ms |
| Latency p95 | 261.7 ms |

### Search Latency Breakdown
- First query: ~1000ms (IndoBERT model warmup)
- Subsequent queries: ~200-300ms
- IndoBERT embedding: ~50ms per query
- SQLite vector search: ~10-50ms

## 3. Chat Performance

### With Gemma 2B (gemma3n:e2b-it-q4_K_M)
| Query Type | Latency | Grounded |
|---|---|---|
| Evidence fast path (requirements) | ~8.6s | True |
| Evidence fast path (duration) | ~5.8s | True |
| LLM path (no fast path) | ~45-52s | False (abstain) |
| Out-of-scope (local_rule) | ~0.1s | False (correct abstain) |

### With Llama 3.2 1B
| Query Type | Latency | Grounded |
|---|---|---|
| All queries | ~10s | False (abstain) |

## 4. Resource Usage

| Component | RAM (idle) | RAM (active) |
|---|---|---|
| Backend (FastAPI) | ~15 MB | ~30 MB |
| IndoBERT worker | ~200 MB | ~200 MB |
| Ollama (gemma3n 2B) | ~1.3 GB | ~4-5 GB |
| Docling worker | ~0 MB | ~500 MB |
| Frontend (Vite) | ~50 MB | ~50 MB |
| **Total (idle)** | **~1.6 GB** | |
| **Total (chat active)** | | **~5-6 GB** |
| **Total (OCR active)** | | **~2 GB** |

## 5. Database

| Table | Rows |
|---|---|
| documents | 64 |
| chunks | 721 |
| knowledge_pipeline_runs | 175 |
| sop_review_events | 712 |
| document_extractions | 193 |
| **Total DB size** | **55.3 MB** |
| Source documents | 60 files, 54.6 MB |

## 6. Known Performance Issues

1. **Docling extraction slow**: ~66s/SOP, CPU-bound (1 thread)
2. **First query slow**: ~1000ms (IndoBERT model warmup)
3. **Chat latency high**: 45-52s for LLM path (Gemma 2B generation)
4. **Memory pressure**: Docling + Ollama together can exceed 8 GB
5. **No concurrent testing**: ThreadPoolExecutor(max_workers=1) for Docling
6. **No 10-SOP batch benchmark**: Only 2 SOPs measured

## 7. Recommendations

1. Run perf_baseline.py on 10 new SOPs for formal baseline (only 1 unprocessed SOP available)
2. Add psutil for peak RAM measurement
3. Test concurrent requests (5-10 simultaneous)
4. Document P50/P95 for search and chat
5. Test retry/timeout/recovery scenarios
6. Consider GPU offloading for Ollama (if GPU available)
7. Consider quantized 7B model for better chat quality

## 8. Commit

- Performance report updated
- perf_baseline.py exists but only tested on 5 already-processed SOPs (all DUPLICATE)
- No new SOPs available for batch benchmark (41/42 processed)
