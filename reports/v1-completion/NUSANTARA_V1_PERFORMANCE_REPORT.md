# NUSANTARA V1 PERFORMANCE REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 7 — Performance & Production Readiness
**Date:** 2026-11-12
**Branch:** codex/fullroot-control-20261007

---

## 1. Available Benchmarks

### SOP Processing (Docling OCR)
- 2 SOPs measured: 132.3s total, 66.1s/SOP average
- 42 SOPs estimated: ~46 minutes total
- Breakdown per SOP: upload (1-2s) + Docling extraction (50-80s) + indexing (5-10s)

### Search Latency (from search eval)
- Mean: 943.6 ms (with backend + IndoBERT worker)
- Median: 304.6 ms
- P95: 363.9 ms
- Note: first query slower (model warmup), subsequent queries faster

### Chat Latency
- Not formally benchmarked (depends on Ollama generation)
- Typical: 5-15s for grounded answers with llama3.2:1b

## 2. Resource Usage

| Resource | Value | Notes |
|---|---|---|
| Backend (FastAPI) | ~15 MB RAM | Idle, no worker |
| IndoBERT worker | ~200 MB RAM | Loaded on first search |
| Ollama (llama3.2:1b) | ~1.3 GB RAM | When model loaded |
| Docling worker | ~500 MB RAM | During extraction |
| Database | 64 docs, ~50 MB | SQLite |

## 3. Known Performance Characteristics

1. **Docling extraction is CPU-bound**: ~66s/SOP on 2 threads
2. **IndoBERT embedding**: 768D, ~4s model load, ~50ms per query
3. **Search**: Hybrid (semantic + lexical), ~200-300ms after warmup
4. **Chat**: Depends on Ollama generation, 5-15s typical
5. **Concurrent requests**: Not tested (10 sync slots in _run_sync_v1)

## 4. Gaps

1. No 10-SOP batch benchmark
2. No peak RAM/CPU measurement during batch
3. No concurrent request testing
4. No P50/P95 documentation for chat
5. No retry/timeout/recovery testing
6. No formal performance report with methodology

## 5. Recommendations

1. Run perf_baseline.py on 10 SOPs for formal baseline
2. Add psutil for peak RAM measurement
3. Test concurrent requests (5-10 simultaneous)
4. Document P50/P95 for search and chat
5. Test retry/timeout/recovery scenarios

## 6. Commit

- Phase 7 report only, no code changes
- perf_baseline.py exists but only tested on 5 already-processed SOPs
