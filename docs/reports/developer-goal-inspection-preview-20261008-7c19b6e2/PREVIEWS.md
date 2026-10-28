# Human goal → inspection preview

Report-owned prototype only; not integrated into Nusantara. No inspection plan has been executed.

Requirements below concern the proposed next static inspection. Eventual repair requirements remain UNKNOWN.

## Perbaiki RAG Nusantara.

**GOAL:** Perbaiki RAG Nusantara.

**UNDERSTANDING:** Petakan retrieval dan grounding sebelum menentukan perbaikan.

**TARGET AREA:** RAG

**INTENT:** INSPECT

**CLARIFICATION:** NOT REQUIRED FOR STATIC INSPECTION

**DISCOVERY NEEDED**

- Baca definisi retrieval configuration tanpa memuat konfigurasi runtime.
- Trace retrieval menuju evidence pack secara statis.
- Periksa aturan grounding dan identifikasi kebutuhan diagnosis terisolasi.

**LIKELY FILES / COMPONENTS**

- app/core/nusantara_config.py
- app/knowledge/rag.py
- app/knowledge/grounding.py

**INSPECTION PLAN**

- Baca definisi retrieval configuration tanpa memuat konfigurasi runtime.
- Trace retrieval menuju evidence pack secara statis.
- Periksa aturan grounding dan identifikasi kebutuhan diagnosis terisolasi.

**EXPECTED EVIDENCE**

- Hubungan configuration → retrieval → evidence → grounding.
- Hipotesis yang didukung source; kualitas data aktual tetap UNKNOWN.

**POTENTIAL RISK:** LOW

**WRITE REQUIRED:** NO

**RUNTIME REQUIRED:** NO

**PROVIDER REQUIRED:** NO

**DATABASE REQUIRED:** NO

**HUMAN DECISION:** NOT REQUIRED

**NEXT STEP:** Tinjau preview, kemudian lakukan hanya inspeksi source yang disebutkan; jangan import aplikasi.

**STATUS:** PREVIEW_READY

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION

## Periksa kenapa jawaban AI kurang akurat.

**GOAL:** Periksa kenapa jawaban AI kurang akurat.

**UNDERSTANDING:** Petakan kemungkinan kehilangan evidence; penyebab belum diketahui.

**TARGET AREA:** Core

**INTENT:** INSPECT

**CLARIFICATION:** NOT REQUIRED FOR STATIC INSPECTION

**DISCOVERY NEEDED**

- Trace pemilihan jalur jawaban dari source API tanpa import aplikasi.
- Bandingkan aturan grounding RAG dan Developer Engine.
- Catat alternatif penyebab dan evidence tambahan yang diperlukan.

**LIKELY FILES / COMPONENTS**

- app/api/routes.py
- app/knowledge/grounding.py
- app/devcore/grounding.py

**INSPECTION PLAN**

- Trace pemilihan jalur jawaban dari source API tanpa import aplikasi.
- Bandingkan aturan grounding RAG dan Developer Engine.
- Catat alternatif penyebab dan evidence tambahan yang diperlukan.

**EXPECTED EVIDENCE**

- Cabang jawaban dan pemakaian evidence.
- Dependency RAG/Model; akurasi aktual NOT_VERIFIED.

**POTENTIAL RISK:** LOW

**WRITE REQUIRED:** NO

**RUNTIME REQUIRED:** NO

**PROVIDER REQUIRED:** NO

**DATABASE REQUIRED:** NO

**HUMAN DECISION:** NOT REQUIRED

**NEXT STEP:** Tinjau preview, kemudian lakukan hanya inspeksi source yang disebutkan; jangan import aplikasi.

**STATUS:** PREVIEW_READY

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION

## Buat Nusantara lebih cepat.

**GOAL:** Buat Nusantara lebih cepat.

**UNDERSTANDING:** Petakan timeout dan pekerjaan sinkron; belum menetapkan bottleneck atau target latency.

**TARGET AREA:** Core

**INTENT:** INSPECT

**CLARIFICATION:** NOT REQUIRED FOR STATIC INSPECTION

**DISCOVERY NEEDED**

- Bandingkan deklarasi timeout dengan consumer source.
- Trace pekerjaan blocking dan dependency provider/RAG secara statis.
- Tentukan desain benchmark sintetis setelah target latency diperjelas.

**LIKELY FILES / COMPONENTS**

- app/core/nusantara_config.py
- app/api/routes.py
- app/devcore/core.py

**INSPECTION PLAN**

- Bandingkan deklarasi timeout dengan consumer source.
- Trace pekerjaan blocking dan dependency provider/RAG secara statis.
- Tentukan desain benchmark sintetis setelah target latency diperjelas.

**EXPECTED EVIDENCE**

- Lokasi timeout dan jalur blocking.
- Bottleneck serta latency runtime belum diketahui.

**POTENTIAL RISK:** LOW

**WRITE REQUIRED:** NO

**RUNTIME REQUIRED:** NO

**PROVIDER REQUIRED:** NO

**DATABASE REQUIRED:** NO

**HUMAN DECISION:** NOT REQUIRED

**NEXT STEP:** Tinjau preview, kemudian lakukan hanya inspeksi source yang disebutkan; jangan import aplikasi.

**STATUS:** PREVIEW_READY

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION

## Periksa konfigurasi provider.

**GOAL:** Periksa konfigurasi provider.

**UNDERSTANDING:** Periksa definisi dan consumer konfigurasi provider tanpa menghubungi provider.

**TARGET AREA:** Configuration

**INTENT:** INSPECT

**CLARIFICATION:** NOT REQUIRED FOR STATIC INSPECTION

**DISCOVERY NEEDED**

- Baca schema provider tanpa membaca credentials/configuration aktif.
- Trace effective configuration owner dari source.
- Trace selection/binding provider dan tandai consumer yang belum dikorelasikan.

**LIKELY FILES / COMPONENTS**

- app/core/nusantara_config.py
- app/core/config.py
- app/models/router.py

**INSPECTION PLAN**

- Baca schema provider tanpa membaca credentials/configuration aktif.
- Trace effective configuration owner dari source.
- Trace selection/binding provider dan tandai consumer yang belum dikorelasikan.

**EXPECTED EVIDENCE**

- Schema → owner → consumer/Provider dependency.
- Provider/model aktual NOT_VERIFIED.

**POTENTIAL RISK:** LOW

**WRITE REQUIRED:** NO

**RUNTIME REQUIRED:** NO

**PROVIDER REQUIRED:** NO

**DATABASE REQUIRED:** NO

**HUMAN DECISION:** NOT REQUIRED

**NEXT STEP:** Tinjau preview, kemudian lakukan hanya inspeksi source yang disebutkan; jangan import aplikasi.

**STATUS:** PREVIEW_READY

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION

## Cari masalah pada Developer Engine.

**GOAL:** Cari masalah pada Developer Engine.

**UNDERSTANDING:** Inspeksi goal routing, source reading, dan grounding; tidak mengasumsikan root cause.

**TARGET AREA:** Developer Engine

**INTENT:** INSPECT

**CLARIFICATION:** NOT REQUIRED FOR STATIC INSPECTION

**DISCOVERY NEEDED**

- Trace goal → intent → read-only actions.
- Periksa workspace/sensitive-file boundary dari source.
- Trace grounding → answer dan cocokkan dengan tes terisolasi yang sudah ada.

**LIKELY FILES / COMPONENTS**

- app/devcore/router.py
- app/devcore/core.py
- app/devcore/workspace.py
- app/devcore/grounding.py

**INSPECTION PLAN**

- Trace goal → intent → read-only actions.
- Periksa workspace/sensitive-file boundary dari source.
- Trace grounding → answer dan cocokkan dengan tes terisolasi yang sudah ada.

**EXPECTED EVIDENCE**

- Pemetaan jalur handled/unhandled dan boundary.
- Gap yang dapat direproduksi dengan fixture non-protected.

**POTENTIAL RISK:** LOW

**WRITE REQUIRED:** NO

**RUNTIME REQUIRED:** NO

**PROVIDER REQUIRED:** NO

**DATABASE REQUIRED:** NO

**HUMAN DECISION:** NOT REQUIRED

**NEXT STEP:** Tinjau preview, kemudian lakukan hanya inspeksi source yang disebutkan; jangan import aplikasi.

**STATUS:** PREVIEW_READY

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION

## Buat AI lebih pintar.

**GOAL:** Buat AI lebih pintar.

**UNDERSTANDING:** Tujuan perlu diperjelas; tidak ada diagnosis.

**TARGET AREA:** UNKNOWN

**INTENT:** AMBIGUOUS

**CLARIFICATION:** REQUIRED

**DISCOVERY NEEDED**

- Tentukan target, gejala dan kriteria sukses.

**LIKELY FILES / COMPONENTS**

- None

**INSPECTION PLAN**

- None

**EXPECTED EVIDENCE**

- None

**POTENTIAL RISK:** UNKNOWN

**WRITE REQUIRED:** UNKNOWN

**RUNTIME REQUIRED:** UNKNOWN

**PROVIDER REQUIRED:** UNKNOWN

**DATABASE REQUIRED:** UNKNOWN

**HUMAN DECISION:** UNKNOWN

**NEXT STEP:** Klarifikasi target dan kriteria sukses.

**STATUS:** CLARIFICATION_REQUIRED

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION

## Restart Nusantara

**GOAL:** Restart Nusantara

**UNDERSTANDING:** Tujuan perlu diperjelas; tidak ada diagnosis.

**TARGET AREA:** UNKNOWN

**INTENT:** RESTRICTED_OR_UNCLEAR_OPERATION

**CLARIFICATION:** REQUIRED

**DISCOVERY NEEDED**

- Tentukan target, gejala dan kriteria sukses.

**LIKELY FILES / COMPONENTS**

- None

**INSPECTION PLAN**

- None

**EXPECTED EVIDENCE**

- None

**POTENTIAL RISK:** UNKNOWN

**WRITE REQUIRED:** UNKNOWN

**RUNTIME REQUIRED:** UNKNOWN

**PROVIDER REQUIRED:** UNKNOWN

**DATABASE REQUIRED:** UNKNOWN

**HUMAN DECISION:** REQUIRED

**NEXT STEP:** Pisahkan inspeksi statis dari operasi berisiko; keputusan manusia diperlukan.

**STATUS:** HUMAN_DECISION_REQUIRED

**REQUIREMENTS SCOPE:** PROPOSED_NEXT_STATIC_INSPECTION

**GOAL RESOLUTION REQUIREMENTS:** UNKNOWN_PENDING_DISCOVERY

**AUTHORIZED OPERATIONS**

- None

**ROOT CAUSE:** UNKNOWN

**BOUNDARIES**

- NO WRITE
- NO RUNTIME
- NO PROVIDER
- NO DATABASE ACCESS
- NO AUTHORIZATION
- NO DEPLOYMENT
- NO EXTERNAL OPERATION
