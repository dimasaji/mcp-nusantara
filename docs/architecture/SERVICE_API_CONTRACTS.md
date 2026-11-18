# SERVICE API CONTRACTS — Nusantara V1

Date: 2026-11-18

## Backend API Endpoints

### Health
- GET /v1/health → {"status":"ok","service":"nusantara-core","version":"0.1.0"}

### Documents
- POST /v1/documents/ingest → {"success":true,"document_id":"...","chunks_created":N}
- Requires: X-Admin-Token header

### Knowledge Search
- POST /v1/knowledge/search → {"query":"...","results":[{document_id,title,score,...}]}
- Requires: X-Admin-Token header

### Chat
- POST /v1/chat → {"session_id":"...","response":"...","grounding":{"grounded":bool},"evidence":[...]}
- Requires: X-Admin-Token header (for operator mode)

### Chat History
- GET /v1/chat/history → {"turns":[...]}
- Requires: X-Chat-Session header

### Pipeline Reviews
- GET /v1/knowledge/pipeline/reviews/{document_id} → review detail
- POST /v1/knowledge/pipeline/reviews/{document_id}/decision → {"version_id":"...","action":"approve|reject|defer"}
- POST /v1/knowledge/pipeline/reviews/{document_id}/metadata → confirm metadata

### Runtime
- GET /v1/runtime/readiness → readiness status
- GET /v1/runtime/verification → verification status

## Error Format
All errors: {"detail":"ERROR_CODE"} with HTTP status code.
Admin required: 403 {"detail":"admin token diperlukan"}
