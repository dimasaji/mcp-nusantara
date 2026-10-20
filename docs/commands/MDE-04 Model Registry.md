Lanjutkan Nusantara FULL-ROOT dari:

C:\Users\dmaza\mcp-starter\.dev\MDE03_CHECKPOINT.json

TASK:
MDE-04 Model Registry — Discovery, Identity Contract & Selection Closure.

STATUS AWAL:
MDE-01 = PASS_SCOPED_STATIC
MDE-02 = DONE_SCOPED_KEEP
MDE-03 = DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS

TUJUAN:
Menentukan bagaimana identity dan lifecycle MODEL saat ini direpresentasikan,
dipilih, diteruskan ke provider, dan dilaporkan kembali ke response.

FOKUS UTAMA:
Menutup ambiguity:

provider_id
    vs
model_id
    vs
ModelSelection
    vs
provider.model
    vs
response.model

ATURAN KERAS:

1. INSPECT BEFORE CREATE.
2. Jangan membuat ModelRegistry sebelum membuktikan abstraction existing tidak cukup.
3. Jangan membuat registry paralel.
4. Jangan mengganti ModelRouter.
5. Jangan mengaktifkan ModelGateway pada API default.
6. Jangan mengubah app/main.py.
7. Jangan mengubah API V1/V2 public schema.
8. Jangan mengubah Trust/Policy/Security.
9. Jangan mengubah RAG.
10. Jangan mengubah embedding/index.
11. Jangan install dependency.
12. Jangan install/download model.
13. Jangan melakukan live cloud/provider call.
14. Jangan membuat provider failover.
15. Jangan mengubah default model selection.
16. Jangan mengubah constructor compatibility.
17. Jangan membuat Core Agent baru.
18. Jangan mulai MDE-05.

INSPEKSI WAJIB:

A. Temukan seluruh model identity representation:
   - ModelSelection
   - provider.model
   - request.model
   - response.model
   - model fields pada schema
   - model fields pada V2
   - ModelGateway
   - ModelRouter
   - Ollama
   - OpenAI-compatible
   - Mock
   - DevCore callbacks

B. Bedakan secara eksplisit:

   PROVIDER ID
   MODEL ID
   DISPLAY NAME
   ROUTING MODEL
   ACTUAL RESPONSE MODEL
   CONFIGURED MODEL
   DEFAULT MODEL

C. Buat Model Identity Matrix:

   Field
   Owner
   Producer
   Consumer
   Source
   Mutable?
   Runtime verified?
   Canonical?
   Evidence

D. Audit semua jalur:

   FAST
   KNOWLEDGE
   TOOL
   OFFLINE
   V2 generation
   ModelGateway
   ModelRouter

E. Cari mismatch yang ditemukan MDE-03:
   1. Aliased MockProvider:
      provider identity berbeda dengan generated model metadata.
   2. Mutable provider identity.
   3. Dictionary registration key berbeda dengan mutable identity.
   4. HTTP adapter menggunakan self.model tanpa response identity validation.
   5. Gateway menerima response yang model-nya berbeda.
   6. Native openai_compatible naming berbeda dengan router preferred openai ID.

F. Tentukan canonical identity contract.

Minimal jawab:

   provider_id:
   model_id:
   capability:
   requested_model:
   selected_model:
   actual_model:
   identity_status:

G. Tentukan status identity:

   DECLARED
   CONFIGURED
   SELECTED
   EXECUTED
   VERIFIED

Jangan menyamakan SELECTED dengan EXECUTED.

H. Audit fallback:

   registered-provider fallback
       ≠
   provider failover

   Pastikan kontraknya tidak berubah.

I. Audit compatibility dengan ModelGateway:
   - sync response
   - async response
   - V2 generate(prompt)
   - existing public signatures

KEPUTUSAN:

Pilih tepat satu:

1. KEEP
   Existing model structures sudah cukup.

2. REFACTOR
   Existing structures cukup tetapi identity contract perlu
   diperkuat tanpa abstraction baru.

3. ADD THIN MODEL REGISTRY
   Hanya jika benar-benar diperlukan dan tidak duplicating ModelRouter.

4. GATE
   Jika keputusan membutuhkan perubahan arsitektur Level C.

Jika KEEP:
- dokumentasikan canonical model identity contract.

Jika REFACTOR:
- implementasi seminimal mungkin.
- pertahankan backward compatibility.
- jangan mengubah default startup.

Jika ADD:
- registry harus menjadi metadata/identity layer,
  bukan replacement ModelRouter.

IMPLEMENTATION RULE:
Tidak ada source change hanya untuk memenuhi nama MDE-04.

VERIFICATION:

Jika discovery/design only:
- focused tests yang sudah ada boleh direuse
- jangan klaim live runtime verification

Jika source berubah:
1. focused tests
2. ModelRouter tests
3. ModelGateway tests
4. V1/V2 compatibility tests
5. full regression
6. source integrity
7. Git diff
8. checkpoint

WAJIB UPDATE:

docs/MDE-04_MODEL_REGISTRY_DESIGN.md
.dev/PROJECT_STATE.json
.dev/TASKS.json
.dev/DECISIONS.jsonl jika ada keputusan arsitektur
.dev/MDE04_CHECKPOINT.json
MDE-04 execution report

STOP SETELAH MDE-04.

JANGAN MULAI MDE-05.