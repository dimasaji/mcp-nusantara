# Build definition and remaining trust boundary

The complete application build must be a closed, independently enumerated artifact inventory. Its expected identity includes canonical schema version, logical input names, roles and content digests. These fields remain separate from repository Git identity, the legacy SOURCE_SNAPSHOT, PID/start, runtime instance and provider identity.

Required roles:

1. APPLICATION_CODE: all application entry points, modules, workers and code used by both NORMAL and ATTESTATION, including dynamically reachable code. Provider implementation bytes are application code; actual provider/model identity is outside this build identity.
2. STATIC_ASSET: application-owned runtime resources, templates and executable/static assets. Runtime data, secrets, RAG databases and model weights are not inspected or included in this task's manifest.
3. DEPENDENCY: complete transitive Python/native dependency artifacts, including extensions and their executable native dependencies. A package version or pyproject declaration alone cannot substitute for bytes actually loaded.
4. INTERPRETER: interpreter, standard-library and applicable native runtime artifacts, with an explicit interpreter/ABI boundary.

This defines the required coverage, but does not enumerate a COMPLETE Nusantara build. The existing source snapshot covers selected source/assets only. Its dependency/interpreter closure and independent load-time inventory are absent. Protected runtime data and external provider state remain separate and unobserved; they cannot be quietly treated as verified build evidence.

The implemented BuildDefinition validates inventory membership independently of digests, rejects malformed/duplicate/unsafe input identifiers and requires all four roles. That is declared inventory consistency, not proof that the declaration encompasses an actual application's execution closure. Presence of four roles does not establish COMPLETE APPLICATION BUILD.

BuildProvenanceOwner records digests from immutable bytes supplied by a server-side artifact consumer, holds PID/start/runtime-instance binding, and returns bounded assessment. It does not retain source contents or expose mutable records. No loader is intercepted or installed. No owner is composed into app.main, an HTTP route, Control Plane or authorization subsystem.

Matching all declared artifacts yields only artifact_binding=VERIFIED. ACTIVE_PROCESS_BUILD and Runtime Identity remain NOT_VERIFIED/NOT_DIRECTLY_VERIFIED even in that case. Serialized/client receipts are rejected. This distinction is intentional; a consumer callback or caller-supplied process context is not independent proof of complete executing process identity.

The remaining engineering requirement is a genuine trusted loader observer that captures the exact bytes/code objects used, ties them to an independently trusted expected artifact inventory, detects every uncovered import/native/artifact input and accounts for relevant execution/global/closure mutation. The current architecture does not supply this witness. Ordinary import-time disk reads and registered handler hashes cannot replace it.

No complete provenance trust root or completeness certificate was invented. No positive complete-application VERIFIED test can be honestly claimed from the implemented artifact foundation. R2-A14 therefore remains BLOCKED. Existing application/service processes were not observed again or reloaded.
