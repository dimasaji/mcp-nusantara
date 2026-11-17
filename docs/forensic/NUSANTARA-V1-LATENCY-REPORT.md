# NUSANTARA V1 LATENCY REPORT

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## 1. Search Latency (from 160-query eval)

| Metric | Value |
|---|---|
| Mean | 192.2 ms |
| Median | 178.9 ms |
| P95 | 261.7 ms |
| First query (warmup) | ~1000 ms |

## 2. Chat Latency

| Query Type | Latency | Notes |
|---|---|---|
| Evidence fast path (requirements) | ~8.6s | Direct source quote, no LLM |
| Evidence fast path (duration) | ~5.8s | Direct source quote, no LLM |
| LLM path (Gemma 2B) | ~45-52s | LLM generation + grounding |
| Out-of-scope (local_rule) | ~0.1s | Immediate abstention |

## 3. SOP Processing Latency

| Metric | Value |
|---|---|
| Avg per SOP | ~66s |
| Docling extraction | 50-80s |
| Indexing | 5-10s |
| Upload | 1-2s |

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

## 5. Known Performance Issues

1. First query slow (~1000ms) due to IndoBERT model warmup
2. Chat latency high (45-52s) due to Gemma 2B generation
3. No concurrent request testing
4. No P50/P95 for chat (only search documented)

---

**Status: PARTIAL (search metrics documented, chat metrics estimated)**
