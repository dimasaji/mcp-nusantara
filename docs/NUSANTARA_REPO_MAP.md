# Nusantara repository map

Updated 2026-11-23 against primary PC repository baseline 71b1e1bf.
Approved physical target: [folder addendum](contracts/NUSANTARA-V1-FOLDER-TARGET-ADDENDUM-20261123.md).
The supplied [NUS-CONTRACT-RECON-001](contracts/NUS-CONTRACT-RECON-001.md) remains DRAFT;
its conceptual tree does not itself authorize new services or data migrations.

| Area | Role and boundary |
| --- | --- |
| backend/app/main.py, backend/app/api | Existing FastAPI/V1 API owners; namespace app.* remains |
| backend/app/hermes | Existing orchestration; external ACP connection remains permission-blocked |
| backend/app/knowledge, backend/app/rag | Existing document ingestion, retrieval, stores and RAG owners |
| backend/app/developer_core, backend/app/devcore | Both existing trees retained; no merge without equivalence evidence |
| backend/app/core | Configuration, identity, evidence and runtime owners |
| backend/app/models, backend/app/execution | Existing provider and governed execution adapters |
| backend/app/context, governance, policy, trust | Existing context/governance owners; no bypass authorized |
| backend/app/v2 | Retained for dependency/tests; no permission to build or enable V2 |
| frontend | React/TypeScript source, component tests, e2e; dist is generated |
| deploy/docker | Dockerfile, Compose, Dockerfile-specific input exclusions |
| config | Non-secret runtime configuration; .env stays private at root |
| service | Windows lifecycle dependency used by supported launchers |
| scripts, developer.py | Operational/evaluation/release tools and local control entrypoint |
| tests, tools | Existing regression fixtures, verification and conversion tooling |
| docs, reports | Documentation, contracts and evidence; test-dependent historical inputs retained |
| data | Persistent data; no database/index migration implied |
| backend/data | Tracked evidence; not automatically duplicate runtime storage |
| nusantara-models | Source worker and local model assets; only intended source belongs in Git |
| model, ollama, .venv* | Runtime/model environments; preserve pending path-aware relocation approval |
| .dev, graphify-out, .tmp-build, pytest-of-* | Checkpoints/graph/test outputs; not additional application source roots |
| mcp-nusantara, mcp-nusantara-upstream, nusantara | Nested Git metadata/local changes; preserve without reset/delete |
| integration, graph-viewer, patch/legacy folders | KEEP_PENDING_REVIEW; names do not authorize deletion |

Directory/root classifications: [folder audit](audit/folder-contract-20261123/RECONCILIATION.md).
The primary repository is C:\Users\dmaza\mcp-starter. pc-final-verification is a
separate worktree with an older baseline and independent changes.

Approved core layout is distinct from completion of all reconstruction and
functional acceptance. Full inventory/dependency proof and pending folders are
not declared complete. Runtime blockers: [PC verification](audit/pc-final-20261123/REPORT.md).
