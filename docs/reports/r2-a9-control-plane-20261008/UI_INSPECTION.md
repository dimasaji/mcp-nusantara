# UI inspection

Existing `control-plane/src/router.tsx` exposes /overview and /system, /evidence, /test, /review, /decision, plus engineering views. `ui.tsx` owns Shell and engineering panels; `human.tsx` owns HumanProvider, navigation, pages, acknowledgement, explicit test selections, Review and Decision.

State is React Context/useState. TanStack Query shares the snapshot query. `api.ts` performs only an allowlisted GET, credentials omitted; Zod `schemas.ts` validates schema version 1. Governance schema explicitly requires read_only=true. `acceptance.ts` manages prerequisites and a material evidence fingerprint excluding refresh timestamps. Material evidence changes invalidate browser decisions. These are useful display controls, not authorization controls.

System/Evidence/Review currently focus on R3.1–R3.14 and historical receipts. Eight human tests start NOT TESTED. APPROVE requires acknowledgements and all human PASS; REJECT/HOLD require reasons. Receipt remains client-side, with a browser timestamp and fingerprint. ABORT is absent. No backend identity, expiry, runtime or replay binding is sent.

Reuse existing panels, navigation, statuses, limitations, errors, query client and CSS. No route migration, dashboard rebuild, framework replacement or styling redesign is required. Extend contracts only after backend policy is approved; do not change existing UI acceptance into runtime authorization silently.

Inspected existing tests: `control-plane/tests/{api,acceptance,human,ui}.test.*` and E2E file inventory. They cover malformed snapshots, backend errors, human/engineering separation, prerequisites, refresh and historical runtime presentation. Fixture-based frontend suites depend on CPLANE_SNAPSHOT_FILE. No suites or fixture generators were executed here.
