# NUSANTARA V1 — Continuation Step 3–5

**Recorded:** 2026-10-10T09:36:59Z  
**Decision state:** V1_HOLD (unchanged)

## Step 3 — Open technical blockers

- **CC-01 HTTP:** BLOCKED. The last focused HTTP attempt and independent socketpair reproduction are already recorded in the baseline. Both show the Python 3.13 Windows socketpair fallback blocked at ccept before route dispatch. No HTTP test result was produced. The environment/access state did not change, so the HTTP test was not repeated.
- **Docker/runtime attestation and CC-06 candidate:** BLOCKED / NOT_VERIFIED. Docker Engine named-pipe access remains denied. No candidate logs, internal port-8000 attestation, model/cache state, or retrieval request can be verified. No credentials were read. Prior scoped CC-06 offline suite remains valid: 28 passed, 5 deselected; it does not verify the active candidate.

## Step 4 — Governance and deployment evidence

- **Official knowledge sources:** historical audit has two Tangerang KTP cases needing review and one missing passport-requirements case. Online discovery found official Government of Tangerang pages and the Directorate General of Immigration FAQ. Tangerang sources differ in specificity and age: the official city page dated 18 Apr 2024 says first-time KTP-el recording uses KK plus birth certificate or latest diploma; the Kecamatan Tangerang page is dated 1 Jan 2022 and lists additional procedural documents. This is a source-review lead, not a governed snapshot. The Immigration FAQ search result lists KTP-el, KK and a supporting civil document for a new passport, with conditional alternative if KTP-el is unavailable; its page could not be opened in this retrieval. No source content was ingested, hashed as a local snapshot, promoted, or treated as an approved oracle.
- **Memory policy:** HOLD. Consent, session ownership, retention, read behavior and whether V1 memory should remain legacy or be disabled require an owner policy decision. No V2 memory implementation was substituted.
- **Symlink security:** NOT_VERIFIED. Historical targeted test skipped because Windows denied symlink creation. sutil behavior query SymlinkEvaluation reports local symlink evaluation enabled; that setting does not prove the process has creation privilege or prove the security check. The test/security implementation was not weakened.
- **Production target:** MISSING. The baseline has no named production target or deployment authorization; no deployment was attempted.

## Step 5 — Current official Evidence Registry snapshot

The official offline collector collect_review_package() was invoked against only the manifest-declared offline artifacts. It did not open the active database/index and made no decision-audit write.

- Package file: uns/step3-5-continuation-20261010-01/package.json
- Package ID: vp_sha256_36bb8d0cdb4ff24fc994d87f8713877caf5a53bfe674d23dd0c9519ddeb574b6
- Package file SHA-256: $pkgHash
- Criteria: 15 NOT_VERIFIED; pass_allowed=false; runtime NOT_VERIFIED.
- Declared evidence validation: 16 VALID, 1 INVALID; current test-run manifest is invalid due to source hash drift (TEST_SOURCE_CHANGED_AFTER_RUN).
- The collector output is the newest package snapshot from this continuation, but it is not acceptance approval. package_id matches the previous snapshot because its fingerprinted evidence is unchanged; the generated timestamp/package-file hash changed.
- Human decision was not written: the official decision route requires an authorized live runtime and current package binding. Neither is available. The human may review the package and choose PASS, FAIL, or HOLD; registry currently blocks PASS.

## Files and state

Only this report and the new run-scoped package were created. Existing reports, tests, application source, runtime configuration, databases, containers, volumes, and previous evidence were not changed. The failed first package-generation command wrote no file; the corrected command produced the package above. The relocated venv emitted its known missing-base-interpreter warning but exited successfully for collection.

## References discovered (not ingested)

- Government of Tangerang City, KTP-el requirements (published 18 Apr 2024): https://tangerangkota.go.id/berita/detail/42185/begini-pembuatan-ktp-el-secara-online-dan-offline-di-kota-tangerang
- Tangerang District, Tangerang subdistrict, KTP-el page (published 1 Jan 2022): https://kec-tangerang.tangerangkota.go.id/persyaratan/ktp-elektronik
- Directorate General of Immigration FAQ: https://imigrasi.go.id/faq

These references require governance review of issuer, applicable jurisdiction, effective date, exact case scope, and approval to ingest before they can close CC-06.
