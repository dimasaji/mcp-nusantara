# BROWSER_END_TO_END_PROOF

**Project:** Nusantara V1
**Contract:** addendum §6 (browser-level evidence, not only unit tests or `curl`), deliverable §12.19 supporting evidence
**Date:** 2026-11-19
**Environment:** Chromium (OpenCode in-app browser) → `http://localhost:5180` (Vite dev) → `http://127.0.0.1:8000` (uvicorn `app.main:app`)
**Screenshots:** `evidence\e2e-01-chat-greeting.png`, `evidence\e2e-02-chat-grounding-refusal.png`
**Raw streams:** `evidence\stream-direct-8000.ndjson`, `evidence\stream-via-proxy-5180.ndjson`

---

## 1. What this document proves, and what it does not

The contract requires proof from a real browser, not from a test client. This document records three interactions performed by driving the actual UI.

| Claim | Proven here? |
|---|---|
| The UI loads and renders from the real dev server | **Yes** — §3 |
| A user can type and submit a question | **Yes** — §3, §4 |
| The answer renders in the chat, from the real backend | **Yes** — §3, §4, both screenshots |
| The grounding guard refuses an unsupported answer in the UI | **Yes** — §4 |
| An anonymous session retrieves no internal SOP evidence | **Yes** — §4, `evidence: []`, "Chat umum belum membaca SOP internal" |
| The approval flow (upload → review → approve) through the browser | **No** — not exercised; covered by the 63-test core gate |
| Streaming latency is acceptable | **No** — §5 measures a real defect |

---

## 2. Preconditions, measured

| Check | Command | Result |
|---|---|---|
| Frontend up | `Invoke-WebRequest http://127.0.0.1:5180` | 200, 532 B, title `Nusantara · Asisten AI` |
| Backend up | `GET /v1/health` | 200 `{"status":"ok","service":"nusantara-core","version":"0.1.0","build_id":"sha256:c0f2b88e…"}` |
| Model loaded | `GET :11434/api/ps` | `gemma3n:e2b-it-q4_K_M`, 4.5 B, Q4_K_M, 5,695,491,872 B VRAM |
| Bind addresses | `Get-NetTCPConnection -State Listen` | 8000 → 127.0.0.1, 5180 → 127.0.0.1, both loopback |

One environmental note recorded for honesty: navigating the browser to `http://127.0.0.1:5180` timed out twice at 60 s, while `http://localhost:5180` loaded immediately. Both resolve to the same listener, which is bound to `127.0.0.1` exactly. The cause was not determined and it is not a product defect — but any monitoring script should use one form consistently.

---

## 3. Case 1 — deterministic greeting

| Step | Action | Observed |
|---|---|---|
| 1 | Open `http://localhost:5180` | UI rendered: sidebar, history, composer, "Mau dibantu apa hari ini?" |
| 2 | Click "Chat baru" | new session created |
| 3 | Type `halo` into `#question`, click "Kirim pertanyaan" | `POST /v1/chat` 200 |
| 4 | Wait for render | **"Halo! Ada yang bisa saya bantu?"** displayed |

Measured through an in-page `fetch` of the identical request: **1,224 ms**, 698 B, two NDJSON lines (`status`, `final`).

Server response:

```json
{"type":"status","message":"Memproses pertanyaan"}
{"type":"final","answer":{"session_id":"probe-stream-ui-1",
  "response":"Halo! Ada yang bisa saya bantu?",
  "provider_status":"local_rule","latency_ms":0,
  "grounding":{"enabled":true,"grounded":true,"reason":"deterministic_response"},
  "trust":{"supports_claim":false,"confidence":0.0,"requires_human":true,
           "evidence_count":0,"evidence_available":false},
  "evidence":[]}}
```

`provider_status: local_rule` — no model was invoked. `evidence: []` — nothing was retrieved. The answer cannot be wrong because it is not generated.

**Screenshot:** `evidence\e2e-01-chat-greeting.png`.

---

## 4. Case 2 — SOP question from an anonymous session

The question is a real SOP question, asked **without** an operator token, from the default source scope displayed in the UI ("Semua knowledge", with the caption "Chat umum belum membaca SOP internal").

| Step | Action | Observed |
|---|---|---|
| 1 | "Chat baru" | |
| 2 | Type `Bagaimana prosedur pengurusan KTP elektronik?`, submit | `POST /v1/chat` 200, `stream:true` |
| 3 | Wait | Answer rendered |

Rendered text, verbatim from the page:

> **Bagaimana prosedur pengurusan KTP elektronik?**
>
> Informasi tersebut belum tersedia secara cukup dalam knowledge base.
>
> Jawaban dokumen belum cukup didukung sumber atau memerlukan peninjauan.
>
> *Detail jawaban*
> Model yang menjawab: gemma3n:e2b-it-q4_K_M
> Jawaban percakapan; tidak dinilai sebagai validasi dokumen resmi.
> Jalur: ollama
> Latensi: 22132 ms
> Waktu: 2026-11-19T03:13:01.401265+00:00

Corresponding server payload (identical request, captured by `curl` to the same endpoint):

```json
{"type":"final","answer":{"response":"Informasi tersebut belum tersedia secara cukup dalam knowledge base.",
 "trust":{"supports_claim":false,"confidence":0.0,"risk_level":"high","requires_human":true,
          "evidence_count":0,"evidence_available":false},
 "provider_status":"ollama","latency_ms":17883,
 "grounding":{"enabled":true,"grounded":false,"reason":"no_evidence"},
 "evidence":[]}}
```

### 4.1 Why this is the important screenshot

Three contract properties are visible in one screen:

| Property | Evidence in the screenshot |
|---|---|
| The model **was** used | "Jalur: ollama", 22,132 ms latency — this is not the deterministic shortcut |
| The guard **refused** the answer | "belum cukup didukung sumber atau memerlukan peninjauan" — no answer was asserted |
| **No internal evidence** reached an anonymous session | trust block `evidence_count: 0`, `evidence_available: false`; UI caption "Chat umum belum membaca SOP internal" |

A product that answers confidently here would be failing its core promise. It abstains instead.

**Screenshot:** `evidence\e2e-02-chat-grounding-refusal.png`.

---

## 5. Case 3 — a stall that only a browser could reveal (finding E2E-1)

This is the reason the contract demands browser proof. Two `curl` runs and one page load produced three different timings for the same server behaviour.

### 5.1 Observations

| # | Client | Path | Server-side `latency_ms` | Wall time to client | Rendered in UI? |
|---|---|---|---:|---:|---|
| 1 | page `fetch` (greeting) | 5180 → 8000 | 0 | **1.2 s** | yes |
| 2 | `curl` direct | 8000 | 17,883 | **18.4 s** | n/a |
| 3 | `curl` through Vite | 5180 → 8000 | 14,529 | **141.6 s** | n/a |
| 4 | UI, SOP question | 5180 → 8000 | 22,132 | **≈167 s** | yes, at ≈167 s |
| 5 | UI, SOP question (first attempt, cold tab) | 5180 → 8000 | 89,351 | **never, > 8 min** | **no — only after manual reload** |

Cases 3 and 4 are the same work: the server reports 15–22 s of processing, the client waits 142–167 s. **≈120–145 s is added on the proxied path.** Case 2 (direct) shows the same server work reaching a client in 18.4 s.

Case 5 is worse. The server persisted the turn at `01:36:07Z` with `latency_ms: 89351`; the tab still read "Menunggu respons model…" at 08:41 local, more than four minutes after the server had finished. Reloading the page rendered the answer immediately, because it had been stored all along:

> Informasi tersebut belum tersedia secara cukup dalam knowledge base. — *Jalur: ollama · Latensi: 89351 ms · Waktu: 2026-11-19T01:36:07.985396+00:00*

### 5.2 What is established, and what is not

| Statement | Confidence |
|---|---|
| The browser path adds ~120–145 s on top of server processing | **Measured, 3 independent clients** |
| One first-request stall exceeded 8 minutes and never recovered without a reload | **Observed once** |
| The answer is persisted correctly even when the UI never shows it | **Verified by reload** |
| The cause is the Vite dev proxy, the NDJSON reader in `api.ts`, or the interaction between them | **Not determined** |
| The same behaviour exists in the production image (no Vite proxy) | **Not tested** — the container has no live frontend check |

The honest statement is that **the served-answer path works and the timing on the dev proxy path does not.** The mechanism needs one controlled experiment (proxy off, UI pointed at `:8000` directly) before anyone "fixes" it.

### 5.3 Why it matters operationally

An operator waiting for an SOP answer sees "Menunggu respons model…" for two to three minutes with no progress signal, and in the worst observed case indefinitely. The obvious human response is to reload — which works, because the backend is fine. That behaviour will read as "the system lost my question" even though nothing was lost.

Recorded as **E2E-1 (HIGH)** in `V1_FINAL_READINESS_REPORT.md`. **No code was changed to address it** — it touches `control-plane/src/api.ts` / `vite.config.ts` and needs approval plus a re-run of the regression gate.

---

## 6. Network evidence

| Request | Status | Note |
|---|---|---|
| `GET /` | 200 | document |
| `GET /src/main.tsx`, 36 `@fs/` module loads | 200 | the UI really is the source tree, not a cached bundle |
| `GET /v1/chat/history` | 200 | 10–14 s, later 239 ms — cold-start cost |
| `GET /v1/control-plane/model-status` | 200 | |
| `POST /v1/chat` (greeting) | 200, 1,222 ms | completed |
| `POST /v1/chat` (SOP) | 200, 84,493 ms recorded | the capture layer marks streamed bodies `unavailable: binary` and the request `failed`; the rendered answer (§4) proves it succeeded. **This is a capture artefact, not a failed request** |

The full 689-byte NDJSON payload is preserved verbatim in `evidence\stream-direct-8000.ndjson` and `evidence\stream-via-proxy-5180.ndjson`, and the two are byte-identical apart from the session id and latency figure.

---

## 7. What this closes

| Contract requirement | Status |
|---|---|
| Browser-level E2E evidence, not only unit tests | **CLOSED** — two rendered conversations, two screenshots |
| Chat path proven end to end | **CLOSED** — UI → proxy → FastAPI → Hermes → Ollama → guard → UI |
| Grounding refusal visible to the user | **CLOSED** — §4 |
| Anonymous session receives no SOP evidence | **CLOSED** — `evidence: []` live |
| Approval flow in the browser | **NOT CLOSED** — deferred, covered by core gate |
| Streaming latency acceptable | **FAILS** — §5 |

**Verdict: the product answers questions through the browser, and refuses to answer what it cannot support. It does so slowly on the dev path, and once it did not do so at all until the page was reloaded.**
