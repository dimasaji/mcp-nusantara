---
name: sop
description: Prepare uploaded SOP PDFs, inspect extraction, find approved sources and obtain cited requirements, procedures and duration through the Nusantara core. Use for any SOP service without filename-specific code.
---

# SOP

Discover trusted operations with `GET /v1/skills`; invoke them with
`POST /v1/skills/{name}/run` and `{"arguments": {...}}`, using the existing
operator authentication. The server supplies role and permissions.

1. `documents.prepare`: pass document ID and current version ID. Upload,
   inbox and retry intake already invoke preparation automatically. QUEUED
   means waiting, not extraction success.
2. `documents.inspect`: inspect state, source page/activity counts and warnings.
3. `knowledge.search`: find approved internal sources; select the intended
   document rather than the first active SOP.
4. `sop.facts`: pass document ID, current version ID and question. Return only
   supported facts and physical source pages. An unsupported question is not
   proof that the whole document lacks an answer.

The executable entrypoint is `knowledge.skills.execute(name, arguments,
role=..., permissions=..., requested_by=...)`. Implementation and typed
contracts live in `app.skills.composition`; execution uses the existing
governed tool registry. Ordinary version-bound SOP chat calls this capability.

Keep publication in the existing operator review flow. These operations do
not approve documents or confirm metadata. Caller arguments cannot install
handlers, execute scripts from PDFs or grant permissions. Trusted modules for
other domains can register through the same domain-neutral runtime.
