# Prinsip Pengembangan — Nusantara Core + Hermes

## 1. Filosofi Utama

### LLM adalah Komponen, Bukan Keseluruhan Sistem
Model bahasa adalah satu bagian dari sistem yang lebih besar. Sistem yang baik menggabungkan:
- Language Engine (pemahaman input)
- Context Engine (kelola konteks percakapan)
- Problem Engine (identifikasi masalah)
- Knowledge/RAG (pencarian evidence)
- Reasoning Engine (perencanaan)
- Workflow Engine (eksekusi terstruktur)
- Policy Engine (keamanan & kontrol)
- Trust Engine (validasi hasil)
- Memory Engine (ingatan jangka pendek & panjang)
- Tool Engine (eksekusi aksi eksternal)

LLM hanya salah satu komponen — sering digunakan diPlanner dan Reasoning, tapi bukan satu-satunya mekanisme.

### Jangan Melompati Fase
Setiap fase harus selesai dan di-test sebelum masuk fase berikutnya. Demo yang terlihat berhasil tapi fase sebelumnya belum di-test = teknologi yang rapuh.

### Jangan Hardcode Jawaban untuk Test
Test harus menguji perilaku sistem, bukan menghafal output. Mock provider wajib digunakan untuk test yang tidak bergantung pada model nyata.

---

## 2. Prinsip Keamanan

### Tool Selalu Lewati Policy
Sebelum tool apa pun dijalankan, Policy Engine harus menyetujui:
- Siapa yang menjalankan (user, roles)
- Apa yang diminta (task, tool)
- Seberapa sensitif datanya
- Berapa risikonya

Tanpa persetujuan Policy, tool tidak boleh dijalankan.

### Hasil Penting Divalidasi Trust
Trust Engine memvalidasi:
- Apakah evidence mendukung claim?
- Apakah ada unsupported claim?
- Apakah hasil sesuai policy?
- Apakah output dalam format yang benar?

Jika Trust gagal, hasil tidak dikirim ke user — clarification, retry, replan, atau human handoff.

### Data Sensitif Diminimalkan
- Tidak ada PII mentah di log.
- Context engine punya privacy filter.
- Memory engine punya TTL dan privacy classification.
- Hanya simpan info yang persistence-nya benarnya dibutuhkan.

---

## 3. Prinsip Pengujian

### Unit Test — Setiap Komponen
Setiap komponen utama harus punya unit test yang:
- Tes semua fungsi utama
- Tes kasus edge
- Gunakan mock provider jika berinteraksi dengan LLM/external service
- Cepat (< 1 detik per test)

### Integration Test — Alur Antar Komponen
Test alur end-to-end:
- Language → Context → Problem → Knowledge → Reasoning
- Workflow transition (start → complete)
- Policy → Tool → Trust

### Evaluation Test — 100+ Skenario
Phase 17 mensyaratkan minimal 100 skenario evaluasi yang mencakup:
- Intent accuracy
- Problem extraction accuracy
- Retrieval accuracy
- Evidence coverage
- Unsupported claim rate
- Tool success rate
- Human handoff accuracy
- Latency, token usage, error rate

---

## 4. Prinsip Arsitektur

### Interface Segregation
Setiap komponen punya interface jelas (Protokol/ABC di Python). Implementasi bisa diganti selama interface sama.

### Provider Independence
- LLM Provider: Ollama, OpenAI, Azure, dsb — semuanya melalui `LLMProvider` interface.
- Vector Store: Chroma, Qdrant, atau memori — semuanya melalui interface retrieval.
- Embedding: Sentence Transformers, OpenAI, atau mock — semuanya melalui interface embedding.

### Persistence Abstraction
State machine (Workflow Engine) punya persistence interface. Bisa di-memory untuk development, Redis/PostgreSQL untuk production. Sama untuk Memory Engine.

### Observability Built-In
- Setiap request punya request_id.
- Setiap tahap punya duration.
- Setiap error tercatat (tanpa PII).
- Metrics bisa diekstrak dari structured log.

---

## 5. Prinsip Iterasi

### Prototype Kecil → Sistem Skala Besar
- Dimulai dengan model kecil (llama3.2:1b di CPU).
- Domain kecil (misal: dokumen government sederhana).
- Data sedikit (beberapa dokumen uji).
- Concurrency rendah (single user).

### Arsitektur Tetap Sama
Yang diperkecil adalah:
- Ukuran model
- Jumlah data
- Jumlah domain
- Concurrency
- Kapasitas infrastruktur

Yang TIDAK diperkecil:
- Interface antar komponen
- Policy & Trust mechanism
- Testing strategy
- Observability

### Release Criteria
Release candidate hanya dianggap siap jika:
- Unit test semua pass
- Integration test semua pass
- Evaluation test menunjukkan metrik yang dapat diterima
- Docker build berhasil
- Security audit selesai
- Performance test menunjukkan latency acceptable

---

## 6. Checklist Sebelum Lanjut ke Fase Berikutnya

Setiap fase harus memenuhi:

- [ ] Semua file yang diminta fase dibuat
- [ ] Syntax check (ruff) clean
- [ ] Type check (mypy) clean (jika berlaku)
- [ ] Unit test semua pass
- [ ] Test coverage ≥ 80% untuk komponen baru
- [ ] Tidak ada hardcoded answer hanya untuk test
- [ ] Mock provider digunakan jika perlu external service
- [ ] Dokumentasi dasar (docstring, README jika perlu) sudah ada

---

*Prinsip ini berlaku untuk semua 18 fase. Tidak ada pengecualian.*
