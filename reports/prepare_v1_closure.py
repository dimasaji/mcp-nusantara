"""One-shot closure metadata/contract preparation; never mutate knowledge databases."""
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
BACKUP = REPORTS / 'v1-closure-backup-20261006'
AUDIT = REPORTS / 'V1_CLOSURE_ORACLE_AUDIT.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if AUDIT.exists():
    raise SystemExit('Preparation already recorded; resume from checkpoint without repeating.')

for relative in ('app/evaluation/datasets/v1_recovery_oracle.json', 'reports/V1_RECOVERY_PROGRESS.json'):
    target = BACKUP / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(ROOT / relative, target)

db_paths = ('data/knowledge/nusantara_knowledge.db', 'data/knowledge/production_knowledge.db')
db_before = {p: digest(ROOT / p) for p in db_paths}
existing_contracts = {p.name: digest(p) for p in (ROOT / 'docs/contracts').glob('*.md')}
oracle_path = ROOT / 'app/evaluation/datasets/v1_recovery_oracle.json'
oracle = json.loads(oracle_path.read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'data/knowledge/official_sources/ktp_el/manifest.json').read_text(encoding='utf-8'))
pins = {p['case_id']: p for p in json.loads((REPORTS / 'V1_RECOVERY_ORACLE_SOURCE_PINS.json').read_text())}
connection = sqlite3.connect((ROOT / db_paths[0]).as_uri() + '?mode=ro', uri=True)
try:
    documents = dict(connection.execute('SELECT document_id, source FROM documents'))
finally:
    connection.close()

audit_cases = []
for case in oracle['cases']:
    status = case['oracle_status']
    metadata = dict(source_authority=None, service_region=None, version=None,
                    effective_date=None, authoritative_status='UNAVAILABLE',
                    metadata_review_status='NOT_APPLICABLE')
    supported = None
    if status == 'PROJECT_FIXTURE':
        text = documents[case['expected_document']]
        supported = all(e in text for e in case['required_evidence']) and case['expected_answer'] in text
        assert supported
        metadata.update(source_authority='project_test_fixture',
                        service_region='LOCAL_EVALUATION_ONLY',
                        version='sha256:' + hashlib.sha256(text.encode()).hexdigest(),
                        authoritative_status='FIXTURE_ONLY_NOT_OFFICIAL',
                        effective_date_status='NOT_APPLICABLE_TO_FIXTURE')
    elif status == 'REVIEW_REQUIRED':
        source = ROOT / case['source']
        text = source.read_text(encoding='utf-8')
        supported = all(e in text for e in case['required_evidence']) and case['expected_answer'] in text
        assert supported and digest(source) == pins[case['id']]['sha256']
        metadata.update(source_authority='official_as_declared_in_snapshot',
                        service_region='Kota Tangerang', version='sha256:' + digest(source),
                        authoritative_status='DECLARED_OFFICIAL_PENDING_GOVERNANCE_REVIEW',
                        metadata_review_status='REVIEW_REQUIRED',
                        effective_date_status='NOT_ESTABLISHED_BY_SNAPSHOT')
        if case['id'] == 'tangerang-ktp-pemula-snapshot':
            entry = manifest['documents'][0]
            metadata.update(published_at=entry['published_at'], retrieved_at=entry['retrieved_at'],
                            source_url=entry['url'], source_declared_hash=entry['sha256'],
                            metadata_review_notes=[
                                'Published date is not an effective date; case is scoped to December 2025 snapshot.',
                                'Manifest hash is declared source content hash, distinct from full Markdown snapshot hash; hash derivation not independently established.',
                                '2022/2024 snapshots contain different requirements/context; current validity and conflicts need owner review.',
                                'Absent from V1 default database; no production ingestion/promotion performed.'])
        else:
            original = ROOT / 'data/knowledge/sop/original/PERMOHONAN_DATA_PRIBADI.pdf'
            declared = '75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50'
            actual = digest(original) if original.exists() else None
            metadata.update(source_declared_hash=declared, original_pdf_hash=actual,
                            original_pdf_hash_matches=(actual == declared),
                            created_date_as_printed='21-Sep-15', revision_as_printed='Agustus 2018',
                            metadata_review_notes=[
                                'SOP PIAK-03 is present in extracted text; ratification date is blank.',
                                'SERVICE and UNIT are blank; SCENARIO kedatangan requires review against document purpose.',
                                'Creation/revision dates do not establish effective date or current legal validity.',
                                'Expected runtime document ID is unknown; no production ingestion/promotion performed.'])
    elif status == 'MISSING':
        metadata.update(metadata_review_status='MISSING', effective_date_status='UNKNOWN',
                        metadata_review_notes=['Official passport requirements, service region and approved version unavailable; stop this case.'])
        assert case['source'] is None and case['expected_answer'] is None
    else:
        metadata.update(source_authority='synthetic_negative_test',
                        service_region='LOCAL_EVALUATION_ONLY', version='synthetic-negative-v1',
                        authoritative_status='NOT_APPLICABLE_NEGATIVE_CASE',
                        effective_date_status='NOT_APPLICABLE')
    case.update(metadata)
    audit_cases.append(dict(case, evidence_text_supported=supported,
                           runtime_document_present=case['expected_document'] in documents,
                           closure_status='AUDITED_WITH_OPEN_GAP' if status in ('MISSING', 'REVIEW_REQUIRED') else 'AUDITED_FIXTURE_OR_NEGATIVE'))
oracle['schema_version'] = 2
oracle['metadata_policy'] = 'Unknown effective dates remain null; snapshot official declarations are not release approval.'
save(oracle_path, oracle)

contracts = {
'RUNTIME-EXECUTION': ('Runtime Execution', '''## Implementasi V1
`app/main.py` menjalankan FastAPI dan mempertahankan router `/v1`. `app/api/routes.py` menyusun tahap Language, Problem, Knowledge, reasoning/provider dan grounding menggunakan Hermes yang sudah ada. `/health` dan `/v1/health` memuat `BUILD_ID` dari `app/core/runtime_identity.py`, ditangkap saat import. Fingerprint meliputi source/assets app, pyproject dan worker; tidak mencakup environment, database, bobot model, atau dependency terpasang.

Konfigurasi umum berasal dari `app/core/config.py::settings`; komponen membaca override environment yang sudah ada. Tidak dibuat configuration truth kedua. `_run_sync_v1` membatasi dua pekerjaan sinkron dan timeout tahap default 30 detik: penuh menghasilkan 503, timeout 504. Timeout HTTP tidak menghentikan thread; slot tetap digunakan sampai pekerjaan selesai. Worker mempunyai batas waktu sendiri.

## Kriteria dan batas bukti
Health hanya membuktikan respons proses. Release harus mencocokkan identity proses dengan candidate dan memverifikasi model, knowledge, chat, workload, restart dan rollback pada target sebenarnya. Candidate lokal recovery lulus pemeriksaan endpoint; container/produksi belum terverifikasi. Perubahan metadata oracle mengubah fingerprint sehingga bukti proses recovery sebelumnya tidak membuktikan build terbaru.

## Rollback
Pulihkan hanya file yang diubah dari backup terikat perubahan; jangan reset working tree. Jalankan candidate terisolasi sebelum mengganti proses produksi. Tidak ada deployment/restart produksi dalam closure ini.'''),
'INTELLIGENCE-MODEL': ('Intelligence Model', '''## Implementasi V1
`app/language/engine.py` memakai semantic intent engine dan IndoBERT client yang sudah tersedia. RAG menggunakan `app/knowledge/indobert_embedding.py`; worker `nusantara-models/indobert_worker.py` memuat `indobenchmark/indobert-base-p1`, embedding 768 dimensi. Route berbagi client semantic intent dengan embedding adapter jika semantic engine tersedia; request pipe client diserialisasi. Ini tidak mengubah bobot atau model.

`app/hermes/agent.py` mempertahankan LanguageEngine, ProblemEngine dan ReasoningEngine. Route membuat `OllamaProvider` dari settings/model request. Provider default mandiri Hermes adalah MockProvider; keberhasilan mock/unit test tidak membuktikan model produksi. Tidak mengganti Hermes/model router atau membuat orchestrator kedua.

## Kriteria dan batas bukti
Error provider/model harus dilaporkan dengan aman, tanpa fallback fakta yang diklaim benar. Verifikasi memerlukan model tersedia, output finite, dimensi sesuai, timeout dan kegagalan provider; kualitas jawaban memerlukan oracle approved. Hasil recovery targeted berhasil setelah worker dibagi; hal ini bukan bukti akurasi resmi atau kapasitas produksi. Tidak mengubah konfigurasi atau memasang dependency pada closure.

## Rollback
Perubahan client recovery mempunyai backup `reports/v1-recovery-backup-20261006/app/api/routes.py`; rollback selektif memerlukan pemeriksaan perubahan pengguna dan regression, bukan penggantian otomatis seluruh file.'''),
'KNOWLEDGE-RAG': ('Knowledge RAG', '''## Implementasi V1
`app/knowledge/engine.py` adalah facade ke `app/knowledge/rag.py` dan SQLiteVectorStore. Default V1 memakai `data/knowledge/nusantara_knowledge.db`, terpisah dari production KB. Parameter `filter` facade saat ini reserved/diabaikan; tidak dijadikan batas authorization. Route menyaring canonical Evidence.score >= 0.50 lalu mengadaptasikannya ke Trust.relevance tanpa memutasi evidence asli. Relevansi bukan authority sumber.

EvidenceGroundingGuard, intent-aware checks dan abstention tetap digunakan. Evidence kosong/tidak mendukung harus menahan klaim; persyaratan, biaya, waktu, prosedur dan alamat tidak boleh diciptakan. Kemampuan guard tidak dianggap sempurna dari fixture tests. Provenance, authority, wilayah, versi, tanggal berlaku, conflict dan approval harus ditinjau sebelum jawaban layanan resmi diterima.

## Oracle dan gate terbuka
`app/evaluation/datasets/v1_recovery_oracle.json` berisi 3 PROJECT_FIXTURE, 1 NEGATIVE_CASE, 2 REVIEW_REQUIRED dan 1 MISSING. Hash snapshot dipisahkan dari hash sumber yang dideklarasikan. Tanggal publikasi/revisi tidak diperlakukan sebagai tanggal berlaku. Dua snapshot Tangerang tidak tersedia di default V1 DB. Syarat paspor/wilayah resmi belum tersedia. Fixture PASS tidak menjadi production correctness.

## Perubahan dan rollback
Tidak ingest/promote production tanpa governance approval. Verifikasi retrieval memakai snapshot DB terisolasi. Closure menambahkan metadata oracle saja, tanpa mengubah pertanyaan/jawaban/evidence; backup berada di `reports/v1-closure-backup-20261006/app/evaluation/datasets/v1_recovery_oracle.json`.'''),
'AGENT-ORCHESTRATION': ('Agent Orchestration Boundary', '''## Boundary dan lifecycle
Kontrak ini mendefinisikan boundary; tidak mengimplementasikan Agent/LangGraph/Graphify runtime. Hermes V1 tetap orchestration foundation. Lifecycle konseptual adalah request tervalidasi -> tahap engine existing -> evidence/trust/grounding -> respons atau kegagalan aman. Kehadiran modul tidak berarti seluruh kemampuan terhubung ke `/v1/chat`.

## Permission dan tool access
Model hanya mengusulkan tindakan; tool terdaftar harus melalui GovernedToolRegistry dengan permission, schema, policy dan approval. Tidak ada arbitrary shell default. Stdio MCP existing hanya expose dua tool baca. Integrasi tool otomatis ke chat V1 belum dibuktikan dan tidak diaktifkan oleh kontrak ini.

## Trust, policy, approval dan audit
Trust menilai dukungan evidence; confidence bukan fakta resmi atau izin eksekusi. Policy terpisah dari execution. Approval harus terikat payload, reviewer berbeda, expiry dan konsumsi sekali. Audit memakai komponen existing dan harus bisa diverifikasi. Production knowledge/source/policy/release tidak dapat berubah otomatis.

## Timeout dan budget
Gunakan batas tahap existing (route 30 detik, dua slot; tool timeout dari ToolSpec default 10 detik), serta batas provider/worker existing. Ini bukan jaminan penghentian side effect saat thread timeout. Settings memuat context tokens 4096 dan context window 10; belum ada bukti global agent budget/token/cost enforcement pada V1. Budget baru wajib proposal dan gate terpisah; tidak dibuat dalam closure.

## Rollback dan penerimaan
Perubahan orchestrator membutuhkan scope, backup, candidate terisolasi, evidence, approval sesuai risiko dan regression. Stop/restart/rollback produksi tetap OPEN sampai diuji pada target yang ditentukan. Keberadaan kontrak tidak memberi izin agent runtime atau menyatakan integrasi PASS.'''),
'TOOL-MCP-API': ('Tool MCP API', '''## Implementasi dan boundary
`app/mcp/stdio_server.py` memakai official FastMCP stdio sebagai adapter ke `app/governance/tools.py::GovernedToolRegistry`. Expose calculator dan current_time_utc; role user dan permissions kosong ditentukan server, bukan client. Error wire disanitasi; detail masuk audit `audit/mcp.jsonl` di data directory. `app/mcp/mcp.py` adalah facade sederhana dan bukan pengganti transport governed; tidak dipromosikan menjadi jalur privileged.

Registry memeriksa nama terdaftar, permission, policy, input schema, approval terikat tool+args, safe_call/circuit breaker, output schema dan audit. Default policy: critical DENY; high/DELETE/EXECUTE REQUIRE_HUMAN; WRITE/EXTERNAL/medium REQUIRE_CONFIRMATION; read/low ALLOW. ToolSpec timeout default 10 detik. Tidak mengubah policy atau memberi permission baru.

## API dan bukti
`/v1` tetap compatibility boundary, ingest privileged dilindungi admin existing. MCP stdio integration recovery 1 PASS membuktikan transport/tool terdaftar pada lingkungan itu; tidak membuktikan semua modul tools terhubung ke chat atau production authorization lengkap. Test schema/error/permission/approval tetap wajib. Symlink escape test mandatory masih SKIP pada Windows tanpa privilege, sehingga filesystem security belum dapat PASS penuh.

## Rollback
Tidak mengaktifkan tool baru atau mengganti registry. Perubahan exposure transport membutuhkan scope, backup, approval risiko, audit dan regression. Dokumen ini dapat dihapus selektif jika perlu; existing contracts tetap dipertahankan.'''),
'TRUST-POLICY-APPROVAL': ('Trust Policy Approval', '''## Implementasi V1
`app/trust/engine.py` menerima relevance; route mengadaptasi Evidence.score menjadi relevance dan mengembalikan enam field publik: supports_claim, confidence, risk_level, requires_human, evidence_count, evidence_available. Issues/details internal tidak diekspos oleh penambahan recovery. Assessment route menggunakan evidence terhadap user_input; bukan sertifikat bahwa setiap klaim final benar. Grounding final tetap pemeriksaan terpisah.

`app/policy/engine.py` dipakai GateIntegration: reasoning tidak grounded atau confidence rendah diblokir; tindakan sensitif memerlukan review. Registry tool memakai default_tool_policy yang sudah ada dengan keputusan ALLOW/REQUIRE_CONFIRMATION/REQUIRE_HUMAN/DENY. Perbedaan interface existing ini tidak diganti atau digabung oleh kontrak. Full policy-to-final-chat action enforcement tidak disimpulkan dari presence atau health status.

## Approval dan audit
`app/approval/queue.py` mengikat approval dengan hash payload, masa berlaku, reviewer berbeda peminta dan konsumsi sekali; default TTL 60 menit. Snapshot approval dipersist ke AuditTrail dan integrity diperiksa saat restore. Implementasi menyatakan dukungan single application worker; competing writers tidak didukung. Persetujuan LLM tidak menggantikan reviewer manusia. Source/prod knowledge/schema/release memerlukan governance sesuai risiko.

## Penerimaan dan rollback
Permission, denial, expired/payload mismatch/reuse approval dan audit integrity perlu bukti tests. Metadata official/verified dalam snapshot tidak sama dengan approved oracle. Keberadaan kontrak tidak menutup deployment/security/oracle gate yang belum dibuktikan. Closure tidak mengubah trust/policy/approval runtime; rollback hanya metadata oracle dan dokumen baru, dengan backup checkpoint terpisah.''')}
created = []
for key, (title, body) in contracts.items():
    path = ROOT / f'docs/contracts/NUSANTARA-{key}-CONTRACT-V1.md'
    if path.exists():
        continue
    with path.open('x', encoding='utf-8') as stream:
        stream.write(f'# NUSANTARA V1 — {title}\n\nTanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.\n\nScope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.\n\n{body}\n\n## Evidence dan change control\n\nSource yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.\n')
    created.append(path.relative_to(ROOT).as_posix())
assert all(digest(ROOT / 'docs/contracts' / name) == h for name, h in existing_contracts.items())
assert db_before == {p: digest(ROOT / p) for p in db_paths}
save(AUDIT, dict(date='2026-10-06', status='AUDITED_WITH_OPEN_GATES', cases=audit_cases,
                 source_pins_unchanged=True, existing_contracts_unchanged=existing_contracts,
                 databases_unchanged=db_before, created_contracts=created,
                 oracle_backup=str(BACKUP / 'app/evaluation/datasets/v1_recovery_oracle.json')))
checkpoint_path = REPORTS / 'V1_RECOVERY_PROGRESS.json'
checkpoint = json.loads(checkpoint_path.read_text())
checkpoint['closure'] = dict(command='docs/commands/NUSANTARA-V1-OPEN-GATES-CLOSURE.md',
    completed_steps=[1, 2, 3, 4], current_step=5, status='IN_PROGRESS',
    contracts_status='SIX_MISSING_DOCUMENTS_CREATED_WITH_OPEN_GATES', created_contracts=created,
    oracle_audit='reports/V1_CLOSURE_ORACLE_AUDIT.json',
    filesystem_evidence='reports/V1_CLOSURE_FILESYSTEM.xml',
    filesystem_status='SKIP_PRIVILEGE', deployment_status='NOT_RUN_DOCKER_UNAVAILABLE_TARGET_OPEN',
    historical_phases_preserved=True, final_regression_runs=0)
save(checkpoint_path, checkpoint)
print(json.dumps(dict(cases=len(audit_cases), contracts_created=len(created), databases_unchanged=True)))
