Lanjutkan Nusantara FULL-ROOT dari checkpoint:
C:\Users\dmaza\mcp-starter\.dev\MDE02_CHECKPOINT.json

TASK:
MDE-03 Provider Registry — Discovery & Contract Closure.

TUJUAN:
Membuktikan bagaimana provider saat ini direpresentasikan, dipilih, didaftarkan,
dan digunakan oleh ModelRouter/ModelGateway tanpa mengubah startup default.

ATURAN KERAS:
1. INSPECT BEFORE CREATE.
2. Jangan membuat ProviderRegistry baru sebelum seluruh provider abstraction existing
   ditemukan.
3. Jangan mengganti ModelRouter.
4. Jangan mengaktifkan ModelGateway pada API default.
5. Jangan mengubah app/main.py.
6. Jangan mengubah API V1/V2.
7. Jangan mengubah Trust/Policy/Security.
8. Jangan install dependency.
9. Jangan mengubah Ollama/model installation/provider availability.
10. Jangan melakukan provider failover nyata.
11. Jangan mengubah RAG, embedding/index, database/schema.
12. Jangan mengubah public API/schema.
13. Jangan membuat Core Agent baru.
14. Jangan memulai MDE-04.
15. Jika implementation source tidak diperlukan, hasil yang sah adalah
    DESIGN + DOCUMENTATION + STATE, seperti MDE-02.

INSPEKSI WAJIB:

A. Petakan seluruh provider abstraction existing:
   - ModelRouter
   - ModelGateway
   - provider classes/adapters
   - Ollama
   - OpenAI/cloud provider jika ada
   - MockProvider/TestProvider
   - callback/provider injection
   - V2 generation path

B. Petakan seluruh registration/discovery:
   - constructor arguments
   - provider dictionaries/registries
   - model selection
   - capability selection
   - provider preference
   - fallback
   - availability/health
   - environment/configuration

C. Buat matriks:

   Provider
   Provider ID
   Model ID
   Capability
   Registration mechanism
   Selection mechanism
   Configuration source
   Availability source
   Fallback behavior
   Consumer
   Runtime verified?
   Evidence

D. Khusus ModelRouter:
   buktikan apakah routing metadata, provider identity,
   dan model identity selalu konsisten dengan provider yang benar-benar
   menghasilkan response.

E. Periksa temuan FULLROOT sebelumnya:
   - coding/reasoning fallback
   - provider.model vs routing model name
   - ModelGateway compatibility
   - V2 degraded fallback
   - provider preference
   - actual provider availability

F. Tentukan apakah existing structure sudah cukup untuk menjadi
   Provider Registry secara konseptual.

G. Bedakan tiga kondisi:
   CONFIGURED
   REGISTERED
   RUNTIME VERIFIED

   Jangan menyamakan ketiganya.

H. Jangan klaim provider live/healthy jika hanya ditemukan secara static
   atau fixture.

KEPUTUSAN YANG HARUS DIHASILKAN:

1. KEEP existing provider structure
2. REFACTOR existing provider structure
3. ADD THIN PROVIDER REGISTRY
4. GATE — jika perubahan membutuhkan keputusan Level C

Jika ADD/REFACTOR diperlukan:
- jelaskan dependency graph
- jelaskan consumer
- jelaskan backward compatibility
- jelaskan public API impact
- jelaskan startup impact
- jelaskan rollback
- klasifikasikan PATCH/REFACTOR/MIGRATION/REPLACEMENT/REBUILD.

Jika source change tidak diperlukan:
jangan coding. Dokumentasikan contract Provider Registry
dan update state/checkpoint.

VERIFIKASI:
- baseline/regression sebelum perubahan
- focused provider/router/gateway tests
- full regression jika ada source change
- static integrity
- git diff
- source hash
- state/task/decision/checkpoint

OUTPUT WAJIB:
1. docs/MDE-03_PROVIDER_REGISTRY_DESIGN.md
2. .dev/MDE03_CHECKPOINT.json
3. update .dev/PROJECT_STATE.json
4. update .dev/TASKS.json
5. update .dev/DECISIONS.jsonl jika ada keputusan arsitektur
6. MDE-03 execution report

STOP setelah MDE-03.
Jangan lanjut MDE-04.