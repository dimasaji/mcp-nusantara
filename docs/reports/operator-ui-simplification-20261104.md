# Operator UI simplification

Baseline: 9de8e2c71ca242e064c2fef8b7230d609c5d39a1. Date: 2026-11-04.

Scope: simplify the existing operator homepage and model/connection settings.
Keep document/chat actions prominent; collapse engineering details; keep all
authorization, backend status, and mutation contracts intact. No login redesign.

Changes:
- Homepage leads with document management and Chat. The four operator questions
  remain, with SOP actions first and system task/evidence detail in disclosures.
- Model settings show model/provider, plain verification wording, refresh and
  Chat actions. Token/provider/model controls are under an explicit disclosure.
- Process identity, revision, verification limits, readiness and maintenance
  remain available in collapsed technical sections.
- Existing tests open model controls before exercising protected operations;
  homepage assertions reflect document links and collapsed technical detail.

Workflow:
- Graphify queried before source inspection for operator navigation/model settings.
- Diagnosis: not applicable, presentation improvement rather than runtime bug.
- TDD: justified skip for reversible presentation changes; no new behavioral
  logic or seam. Adapted existing public rendering tests to new labels/disclosures
  without removing token, error, model-selection or backend-contract assertions.
- Design: reuse existing modules, queries, links, and native details/summary.
- Standards review: independent reviewer found zero actionable violations.
- Spec review: found outdated tests for labels/collapsed model controls; adapted.
  Independent re-review confirmed zero remaining findings in presentation scope.
  A static status role initially interfered with health-loading announcements;
  changed it to a polite live region while preserving actual loading status.

Validation commands from control-plane:

```powershell
node node_modules/vitest/vitest.mjs run tests/operator.test.tsx tests/assistant.test.tsx tests/settings.test.tsx --pool=threads --maxWorkers=1 --minWorkers=1
node node_modules/typescript/bin/tsc --noEmit
```

Assistant 27/27, operator 8/8, and settings 8/8 passed (43 tests total).
Final TypeScript check passed (exit 0).
Scoped `git diff --check` passed. Browser layout and live API behavior are not
verified by fixture-based UI tests. Preexisting SOP review/backend work preserved.
No production build or service restart performed.

Graphify update was invoked; extraction completed for 322 uncached files.
Overall update did not finish and was interrupted; graph freshness is unverified.
Warnings concern optional PDF tooling and an
existing unrelated syntax error in patch_embedding_identity.py.
