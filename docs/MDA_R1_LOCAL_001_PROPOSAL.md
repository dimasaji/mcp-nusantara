# R1-LOCAL-001 — preliminary effective configuration proposal

State PLANNED; NOT_AUTHORIZED; implementation NOT_STARTED. Level C, HIGH architecture/configuration wiring risk. Integrity precondition BLOCKED: two protected SQLite sidecars disappeared after the initial successful checkpoint check. Do not begin implementation until this difference is explained and a safe baseline is accepted; do not restore production files automatically.

Objective: reuse existing NusantaraConfig validated snapshot/provenance and cached configuration owner to compose one immutable effective context before API dependencies. Inject into existing provider/KnowledgeEngine consumers, preserve explicit request/constructor overrides and distinguish omitted top_k. Do not duplicate loader/root/registry.

Proposed local file scope:

- app/core/nusantara_config.py — current SHA256 3d18304750d9b43e6cf33a19f5f1d73ea5b05bf2b22d9686deecd6fd4371911d
- app/core/config.py — current SHA256 996bfaed79b989576ec31dd10f9d94f5bc419466dc67e4da5c54f7666e3af5b6
- app/main.py — current SHA256 40debcba1d369cc25838ae7ac46cb145a845d0e7170f3a25c016fb867e24743c
- app/api/routes.py — current SHA256 ee5eceefbc479eaf4426f2f8d97bde674a6a951b139dc861dcd5f6701339c8a4
- app/api/v2_routes.py — current SHA256 85548ab3f8573a0e5900e4f8650f499b7864782b16bc374f927a1589c62ca8a7
- app/models/ollama.py — current SHA256 73f4f268d655ee425b25b0a4b399bd4c503c773d1a7d5949831e2fbb34ad904b
- app/knowledge/engine.py — current SHA256 eb7836d0edf858303bbc14cce30cdfe007fd7f22fa9521489a71c2447c26a43b
- tests/test_configuration_contract.py — current SHA256 bc4478e0100bab03d2dc8580cbf6a8e29176b7fdbc690795a745a732551d7123
- tests/test_configuration_integration.py — current SHA256 2becf4883d6eccc9cd364c64a7b9be1638f5a8cd04136d8d4229e8399f2d680b
- tests/test_model_router_configuration.py — current SHA256 b0ce4e26bec018425b8965fefb616c2bb5f001cc7b7990d9c94064c744397f61

Configuration precedence proposal: defaults < explicitly selected JSON < selected existing dotenv compatibility aliases < selected process ENV < explicit bootstrap overrides. Supported request overrides are separate invocation evidence, not mutations of the shared snapshot. Preserve actual layer attribution, reject same-layer alias conflicts, and never resolve/display secret credentials or derive permissions from config.

Direct impact: existing config owner, API construction order, provider constructor/options and facade defaults. Transitive impact: V1/V2/Hermes/RAG/embedding handoff and compatibility tests. Preserve actual canonical fixed IndoBERT/SQLite profile, existing DB paths, embedding model/dimension, 0.70/0.30 weights, relevance/grounding gates, unsupported-field rejection, public schemas/auth/audit/data-root ownership. Explicit model equal to legacy default must remain explicit. No security/approval/policy changes, production environment/data/schema/index mutations, model installs, worker/service startup or UI/Docker/MCP production activation.

Test plan: STATIC consumer/provenance/build/hash review; UNIT/FIXTURE precedence/immutability/safe serialization; INTEGRATION/FIXTURE real constructors/payload/query with replacement store/worker/HTTP transport; REGRESSION/FIXTURE routing/governance/public projection and guarded assembly. No tests weakened. After approved source edits run Graphify AST update. LIVE_RUNTIME requires separate scoped authorization and safe identity/index prerequisites. Fixtures cannot produce production CONFIGURATION/RUNTIME_CONSUMPTION VERIFIED.

Rollback before implementation: snapshot exact approved source/test hashes, build and protected data; preserve inherited dirty edits. On failure stop, revert only owned approved patch after concurrency checks, rerun scoped tests and verify restored hashes. No reset/clean or automatic production DB restore. Extra files/protected behavior require amended approval.

Dependencies: R1 -> R2 -> R3 -> R4 -> R5 -> R6 -> R7 recommended order; R2/R3 independently depend on R1, R4 joins R1/R2/R3, R5 follows R4, R6 requires all safe gates, R7 requires verified evidence and human acceptance. Production index PARTIAL/UNKNOWN prevents live readiness but does not require automatic repair before planning local R1.

Current required decisions: review integrity difference/accept safe rebaseline after investigation; then explicitly authorize R1-LOCAL-001 exact local scope. This proposal is preliminary while protected baseline is BLOCKED; approval must not waive unknown production state. No automatic MDE10.
