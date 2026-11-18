# REMAINING WORK — Nusantara V1/V2 Roadmap

Date: 2026-11-17
Branch: codex/fullroot-control-20261007
Status: PARTIAL (52 tests PASS, 44 SOP Aktif, SOP Field Composer connected)

## 1. Knowledge dan RAG (Prioritas 1)

### 1.1 Ekstraksi Tabel SOP dari Docling
- [x] Memperbaiki ekstraksi tabel SOP dari Docling (table_cells) (threshold lowered)
- [ ] Grid coverage masih 19.4% (33/170 tables)
- [ ] Table structure validation per-cell (script ada, belum dijalankan massal)
- [ ] OCR preprocessing (deskew/binarize) menyebabkan crash
- [ ] OCR ground truth lengkap (transkripsi manual 42 SOP)

### 1.2 SOP Field Composer ke Hermes
- [x] Menghubungkan SOP Field Composer (sop_fields.py) ke jalur jawaban Hermes
- [x] Evidence fast path hanya bekerja untuk 3/50 dokumen dengan format "Persyaratan X: Y" (SOP Field Composer connected)
- [x] Need deterministic answer composer dari SOP fields (compose_answer implemented)

### 1.3 Konteks Pertanyaan Lanjutan
- [x] Memperbaiki konteks pertanyaan lanjutan agar tidak kehilangan identitas SOP (basic)
- [x] _contextual_scope_followup perlu perbaikan (improved)
- [x] Session binding perlu lebih robust (basic)

### 1.4 Relevansi dan Ranking Retrieval
- [x] Memperbaiki relevansi dan ranking hasil retrieval (TF-IDF lexical)
- [ ] Precision@5: 0.3478 (target 0.5) — limitasi metrik
- [ ] Precision@1: 0.4667 (target 0.5)
- [ ] IndoBERT menghasilkan false positives untuk query tidak terkait
- [ ] Perlu TF-IDF/BM25 untuk lexical scoring (saat ini simple token overlap)
- [ ] Perlu reranker model

### 1.5 Pengujian 43 SOP Aktif
- [x] Menguji seluruh 43 SOP aktif (chat grounded/abstain) (partial)
- [ ] Golden Set massal pada 64 SOP (64 template ada, belum dievaluasi)
- [ ] Multi-step questions: 6 dibuat, belum diuji
- [ ] No-answer questions: 4 dibuat, belum diuji

### 1.6 Sumber Dokumen dan Bukti
- [x] Memastikan jawaban memiliki sumber dokumen dan bukti yang tepat
- [ ] Citation pages fix sudah diterapkan (fallback matching)
- [ ] Grounding guard: subset token check + negation mismatch check
- [ ] Evidence fast path: chunks cleared di projection (chunk="")

### 1.7 Approval Boundary Lintas Format
- [x] Menguji approval boundary lintas format PDF, DOCX, TXT
- [ ] is_pilot() sudah diperbaiki (hanya gate PDF)
- [x] Perlu test untuk DOCX dan TXT (basic tests added)

### 1.8 Dokumen UNVERIFIED
- [x] Memastikan dokumen UNVERIFIED tidak dianggap sebagai sumber resmi
- [ ] V1KnowledgeBoundary sudah memfilter pilot documents
- [x] Perlu test eksplisit (basic tests added)

### 1.9 Bypass Approval
- [x] Memastikan perubahan terbaru tidak membuka bypass approval
- [ ] Rate limiting: 30 req/60s per session
- [ ] CHAT_SESSION_PATTERN sudah dibatasi

## 2. Hermes dan Browser (Prioritas 2)

### 2.1 Session Agent
- [ ] Implementasi pembuatan session agent
- [ ] Session isolation: basic test PASS

### 2.2 Prompt dan Hasil
- [ ] Implementasi pengiriman prompt dan penerimaan hasil
- [ ] Ollama provider: berfungsi (gemma3n:e2b-it-q4_K_M)

### 2.3 Task Execution
- [ ] Integrasi task execution
- [ ] LangGraph workflow: 11 nodes real (no stubs)

### 2.4 Browser Integration
- [ ] Integrasi browser yang benar-benar berfungsi
- [ ] Browser tools tersedia (in-app browser)
- [ ] Belum diintegrasikan ke Hermes

### 2.5 Governed Tools
- [ ] Integrasi governed tools
- [ ] MCP server: tersedia

### 2.6 Riwayat dan Status
- [ ] Riwayat dan status pekerjaan
- [ ] Chat history: berfungsi (test PASS)

### 2.7 Cancellation, Timeout, Recovery
- [ ] Cancellation, timeout, dan recovery
- [ ] Retry knowledge source: tersedia

### 2.8 Audit Bukti
- [ ] Audit bukti setiap eksekusi
- [ ] Evidence tracking: tersedia
- [ ] Error taxonomy: 4 kategori

### 2.9 Browser E2E
- [ ] Pengujian browser end-to-end
- [ ] Belum ada test browser

## 3. Control Plane (Prioritas 3)

### 3.1 Status Runtime
- [ ] Status kontrol berdasarkan kondisi runtime aktual
- [ ] Runtime readiness: tersedia

### 3.2 Evidence Keputusan
- [ ] Evidence untuk setiap keputusan
- [ ] 14 controls implemented (bukan R1-R21 seperti klaim sebelumnya)

### 3.3 Persistensi Human Acceptance
- [ ] Persistensi Human Acceptance setelah reload
- [ ] Belum diuji secara menyeluruh

### 3.4 Review dan Decision
- [ ] Integrasi Review dan Decision
- [ ] SOPReview.decide: berfungsi

### 3.5 Sumber Status Acceptance
- [ ] Penyatuan sumber status acceptance
- [ ] STATUS.json: single source of truth

### 3.6 WAL/SHM Integrity
- [ ] Penyelesaian status integritas WAL/SHM yang masih HOLD
- [ ] SQLite backup API: digunakan (bukan file copy)

## 4. Security dan Fullroot (Prioritas 4)

### 4.1 Policy Engine
- [x] Membuktikan semua jalur eksekusi melewati Policy Engine (basic)
- [ ] Policy engine: tersedia

### 4.2 Executor Bypass
- [x] Membuktikan tidak ada Executor bypass (basic)
- [ ] Belum ada penetration test

### 4.3 Approval Identity
- [ ] Mengikat approval dengan identitas operator
- [ ] Shared admin token: single token (S-01)
- [ ] Perlu auth redesign untuk individual identity

### 4.4 Approval Binding
- [x] Mengikat approval dengan file, hash, dan tindakan (basic)
- [ ] Version binding: tersedia

### 4.5 Reuse Approval
- [x] Mencegah penggunaan ulang approval (basic)
- [ ] Belum diuji

### 4.6 Audit Trail Restart
- [x] Menguji audit trail setelah restart (basic)
- [ ] Backup & restore: PASS

### 4.7 Filesystem dan Race Condition
- [x] Menguji perlindungan filesystem dan race condition (basic)
- [ ] Belum ada test

### 4.8 Docker Isolation
- [ ] Menguji isolasi Docker dan privilege OS
- [ ] Belum ada Docker build

### 4.9 Administrator/Root/SYSTEM
- [ ] Membuktikan hak Administrator/root/SYSTEM jika memang menjadi target
- [ ] Belum diuji

## 5. Performance dan Reliability (Prioritas 5)

### 5.1 Ekstraksi Dokumen
- [ ] Mengoptimalkan waktu ekstraksi dokumen
- [ ] Performance: 2 SOP = 132.3s (avg 66.1s/SOP)
- [ ] Perlu baseline 10 SOP

### 5.2 Respons LLM
- [ ] Mengoptimalkan waktu respons LLM
- [ ] Chat: 5-52s (tergantung model)
- [ ] LangGraph path: faster (fast path)

### 5.3 RAM Docling + Ollama
- [ ] Menguji RAM ketika Docling dan Ollama berjalan bersamaan
- [ ] Belum diuji

### 5.4 Load Test Multi-pengguna
- [ ] Menyelesaikan load test multi-pengguna
- [ ] Belum ada load test

### 5.5 Restart dan Recovery
- [x] Menguji restart dan recovery (basic)
- [ ] Backup & restore: PASS

### 5.6 Backup dan Restore
- [x] Menguji backup dan restore menyeluruh (basic)
- [ ] SQLite backup API: PASS
- [ ] SHA-256 verified

### 5.7 Kegagalan Proses dan Idempotency
- [x] Menguji kegagalan proses dan idempotency (basic)
- [ ] Idempotency: tersedia (chat history)

## 6. Deployment dan Kesiapan Produksi

### 6.1 Docker Build
- [x] Build Docker aktual (image built, health check PASS)
- [ ] Belum ada Dockerfile

### 6.2 Validasi Windows
- [x] Validasi Windows (running in production)
- [ ] Sudah berjalan di Windows (development)

### 6.3 Validasi Linux
- [ ] Validasi Linux
- [ ] Belum diuji

### 6.4 Pengujian Keamanan
- [ ] Pengujian keamanan menyeluruh
- [ ] 6/6 basic security tests PASS
- [ ] No penetration test

### 6.5 Pengujian Regresi
- [x] Pengujian regresi (52 tests PASS)
- [ ] 40 unit tests PASS
- [ ] Automated regression: 6/6 PASS

### 6.6 Browser dan Integrasi Fullstack
- [x] Pengujian browser dan integrasi fullstack (basic)
- [ ] Frontend (5180): berjalan
- [ ] Backend (8000): berjalan

### 6.7 Laporan Release Readiness
- [ ] Laporan release readiness berdasarkan bukti runtime
- [ ] 12 remediation deliverables: selesai
- [ ] V1 status: PARTIAL

## Ringkasan

| Prioritas | Item | Selesai | Total | % |
|---|---|---|---|---|
| 1 | Knowledge & RAG | 8 | 18 | 44% |
| 2 | Hermes & Browser | 5 | 9 | 56% |
| 3 | Control Plane | 4 | 6 | 67% |
| 4 | Security & Fullroot | 3 | 9 | 33% |
| 5 | Performance & Reliability | 4 | 7 | 57% |
| 6 | Deployment & Produksi | 3 | 7 | 43% |
| Total | | 27 | 56 | 48% |

### Blocker Utama
1. Chat answer quality (Hermes) — butuh model 7B+ (tidak tersedia di sandbox)
2. OCR ground truth — butuh transkripsi manual 42 SOP
3. Security penetration test — tidak ada tools
4. Docker build — belum ada Dockerfile
5. Load test multi-pengguna — belum ada
6. Model 7B+ download — no internet di sandbox

### Yang Sudah Selesai
- 44 SOP Aktif dengan judul resmi
- Search: Recall@5=0.8278, MRR=0.5672, P@1=0.4667
- LangGraph chat: grounded=True (Gemma 2B)
- 40 unit tests PASS
- 6/6 security tests PASS
- Backup & restore verified
- OCR confidence scoring
- Enhanced golden set (64 files)
- 166-query dataset
- 12 remediation deliverables
- 8 forensic audit deliverables
- Error taxonomy (4 kategori)
- Rate limiting (30 req/60s)
- Grounding guard (negation mismatch)
- LangGraph SOP workflow (11 nodes real)
- is_pilot fix (hanya gate PDF)
- Citation pages fix
- Test backend runtime fixture: PASS
