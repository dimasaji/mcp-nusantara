# Operator UI simplification

Upstream baseline: `47448958068b0b2f17bac170f638df125d10561e`.

## Requested behavior

- Daily operator navigation exposes Beranda, Dokumen, Persetujuan and Riwayat aktivitas.
- Engineering phase/gate and acceptance identifiers are not the default content of technical pages. Operators explicitly open technical details when investigating.
- Existing technical views remain available. This display choice is not authentication or a role restriction.
- Existing backend policy, acceptance criteria, decision checks, source verification and execution authorization remain unchanged.
- Missing evidence and blocked actions must remain visible and cannot become a successful status through presentation changes.

## Implementation

`TechnicalView` defers rendering technical pages until requested. Technical navigation is collapsed by default. `/dashboard` remains the daily operator home; `/overview` and `/system` retain the previous System view behind the technical-details action, preserving the acceptance workflow's System route. Review route aliases use the existing Human Control presentation and the same ExecutionReview owner. The dashboard summarizes stored checks without listing their identifiers; complete gate evidence remains in its technical drawer. Blocker reasons remain visible with their identifiers in the technical drawer.

## Workflow evidence

- Graphify: attempted `graphify query 'operator control plane evidence'`; CLI unavailable. Earlier connector read of the 70 MB graph returned no content. Source traversal used router, settings, operator, sidebar and existing acceptance/readiness owners instead. `graphify update .` also fails because the CLI is unavailable; graph is not updated.
- Diagnosis: not applicable; this is a requested presentation feature, independent of the unresolved local SOP-click issue.
- TDD: test interface is rendered operator navigation and technical-details interaction. It catches disclosure of technical navigation and preservation of disabled controls; it cannot prove a live backend. The navigation test failed because the technical link was exposed, then passed after the UI change. Existing acceptance and decision tests cover unchanged decision behavior with fixtures.
- Design: one presentation wrapper; no backend/schema/configuration changes. Known engineering renderers are preserved.
- Review: independent Standards and Spec reviews both finished with no unresolved findings after fixing System-stage routing and raw snapshot blocker exposure.

## Verification

- Navigation red/green: `npm test -- tests/operator-simplicity.test.tsx`. Initially failed on the exposed technical navigation link; passes after the change.
- Snapshot red/green: `npm test -- tests/operator.test.tsx -t 'summarizes snapshot'`. Initially failed because `R4: LOCKED` was visible; passes after the change.
- Targeted regression: seven suites covering navigation, technical-details interaction, settings, acceptance, real decision controls, verification pages and ATTESTATION routing: **59 passed**. The separate snapshot test also passed.
- Final `npm test`: **190 passed, 4 failed, 194 total**. A pristine baseline worktree using the same dependencies returned **187 passed, the same 4 failed, 191 total**. Three engineering-console tests require historical report archives not materialized in this frontend snapshot. The existing Workspace test expects `Ollama · fixture-local`, which is absent in the baseline UI as well. No additional failure was introduced.
- `npm run build`: TypeScript and Vite production build pass; existing bundle-size and dependency annotation warnings remain.
- `git diff --check`: pass.
- Browser verification could not run: no installed Chromium executable; `npx playwright install chromium` repeatedly received an empty/truncated download. No browser screenshot or live-backend claim is made.
- Graphify query/update: not run successfully; CLI missing and graph unchanged. Run `graphify update .` in a full development checkout before treating the graph as current.

This change does not implement login, Google authentication, roles or Super User accounts. It does not claim to repair the local SOP question that has no observed network trace.
