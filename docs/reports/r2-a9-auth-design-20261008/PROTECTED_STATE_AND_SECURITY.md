# Protected state and architecture preservation

NORMAL: preserve existing app.api.routes, v2_routes, /v1/chat, /v2/chat and /v2/dev, provider/model selection, configuration precedence and current production audit behavior. The proposed owner/actor/permit bridge must not install in NORMAL or legacy evidence-only composition. No new profile or deployment setting is introduced by this design.

ATTESTATION: instantiate only existing memory AuditTrail/ApprovalQueue plus narrow policy/identity adapter. Import existing classes directly; never acquire audit via v2_routes. Do not import KnowledgeEngine, LanguageEngine, RAG, protected storage owners or public API modules. No production file sink, credential database or audit persistence. A local OS IPC endpoint is not a database or alternate application listener; its security requires separate approval and isolated tests.

Do not invoke current project() for this workflow; its existing snapshot path hashes protected SQLite/WAL/SHM. A future scoped evidence function must read only explicitly authorized bounded report/test artifacts and in-process identity. NORMAL historical projection can remain unchanged. In discovery none of the projection, database, RAG or provider paths was invoked.

Origin/Host/peer restrictions are defense in depth, not actor authentication. Existing Vite proxy does not prove browser identity, and its Host rewrite does not bind Origin. Mutating intentions, if implemented later, must use exact allowlisted UI/runtime origins, content type and strict bounded schemas; an intent can never arm or invoke. No wildcard mutation origins. No change to Vite/CORS/configuration is silently authorized. If installation requires origin behavior changes, return for human approval.

No arbitrary URL/prompt/provider/model/database/RAG/config/command accepted. Evidence paths are server-owned allowlisted paths, symlink/path traversal and oversize inputs rejected. Do not let reviewer strings, statuses or evidence fingerprints establish trust. UI is an observer/requester even after this adapter exists.

Threat boundary: same permitted Windows user, compromised local account, injected application process or compromised trusted operator tool can bypass assurances about human intent. No claim against hostile kernel/admin or full-process code tampering. Scoped code hash excludes mutable globals/closures; binding is evidence of its stated scope, not comprehensive tamper resistance. Fail closed if stronger requirements are needed.

Memory-only audit may be lost at process termination, does not prove durable chronology, and cannot support recovery/rearm. Existing hash chain establishes internal linkage, not an external trusted timestamp or immutable storage. No claim of stronger audit guarantees.

No live service probe/restart/arming/generation, configuration change, provider/model operation, protected-file mutation or Git mutation occurred. Deployment/lifecycle and live verification remain separate human gates.
