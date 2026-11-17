# S-09: Error 500 Investigation

**Date:** 2026-11-17

## Finding

No actual HTTP 500 errors from the Nusantara backend. The "Layanan belum tersedia (500)" reported by the user was caused by Ollama being down (Ollama returns 500 on /api/tags when starting up).

## Evidence

- Backend log: 0 HTTP 500 lines
- 40 "Exception" lines are all `_ProactorBasePipeTransport._call_connection_lost()` (Windows async I/O cleanup, not real errors)
- Ollama log: multiple 500 errors on GET /api/tags (Ollama starting up)

## Root Cause

Ollama process died (likely due to memory pressure from Docling extraction). Backend tried to call Ollama for model listing → 500.

## Solution

1. Restart Ollama: `ollama serve`
2. Restart backend: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
3. Verify: `curl http://127.0.0.1:8000/v1/health/detail` → should show `llm status: ok`

## Status: RESOLVED

- S-09 original issue: `f"...{exc}"` in routes.py lines 1424, 1510, 1561 — ALREADY FIXED (internal_error() sanitizes exceptions, logs server-side only)
- 500 errors from Ollama /api/tags — infrastructure issue (Ollama starting up), not a backend bug
- Backend has 0 HTTP 500 lines in logs
- 40 "Exception" lines are all `_ProactorBasePipeTransport._call_connection_lost()` (Windows async I/O cleanup)

**Both sub-issues resolved.**
