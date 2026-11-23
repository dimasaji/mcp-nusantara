# VPS Release and Rollback Plan — Nusantara V1

- Commit SHA under review: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Active production commit: `b44b01e7d24efbd5ff7f4830cc71624b5aa4bf7f` (`g_active_commit`)
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Prepared: 2026-11-23T22:23:35Z

## Gate G verdict

**PASS (plan complete) / NO-GO (deploy not authorized)** — the release delta is minimal and rollback is code/image only, but deployment preconditions are not met. No deploy, restart, port change, image build, or service modification was performed in this stabilization.

## Release delta

`g_release_diff` confirms only two files differ from active `b44b01e7`:

- `backend/app/main.py` +1 line: additive `@app.get("/readyz")` alias to `readiness_check`.
- `tests/test_readyz_contract.py` +34 lines: red/green contract test.

No DB migration, dependency change, schema change, or destructive file operation is included. Rollback risk is therefore low at the code level.

## Current production state (do not disturb here)

- Backend PID `7680`, `127.0.0.1:18201`; frontend PID `7740`, `127.0.0.1:15274`; Ollama PID `1090`, `127.0.0.1:11434` (`a_processes`, `c_ports_after_isolated`, `e_ports_after_stop`).
- Active DB `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/verify-final/staging-db/verify.db`, size `94208`, mtime `2026-11-23 17:53:05.461642521 +0000`, SHA-256 `32eb169f79dfe021e5dd4fd007e43e816369dcd80685c7b8dc4375df7b9cf122`, `quick_check=ok`, `9` tables (`e_db_stat`, `e_db_hash`, `e_db_pragmas`).
- Active `/health` HTTP 200 with build ID `sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331` (`e_active_after_stop`).
- Active `/readyz` still 404; the alias is only in the RC and was verified on isolated ports (`a_readyz_status`, `c_readyz_alias`).

## Deployment preconditions (all currently unmet)

1. Owner approval of the final review commit and explicit permission to deploy.
2. PC PIAK-03 acceptance `GO` per `PC_PIAK03_ACCEPTANCE_HANDOFF.md`; current `knowledge=NOT_VERIFIED`, `official_oracle=REVIEW_REQUIRED`, `approval=REVIEW_REQUIRED`.
3. Fix the Docker image before any container deploy:
   - `scripts/healthcheck.py` is `0` bytes (`g_deploy_facts`), so `HEALTHCHECK ... CMD python scripts/healthcheck.py` cannot validate the service.
   - `deploy/docker/Dockerfile:13-14` points to `/opt/indobert/bin/python` and `/opt/indobert-worker/indobert_worker.py`, but no `COPY` or approved mount places `indobert_worker.py` at `/opt/indobert-worker/`; grounded ingest cannot work from this image as written.
   - Runtime dependencies are installed with mostly unpinned `pip install` commands (`Dockerfile:8,11-12`); only `haystack-ai==3.4.1` is pinned. This is not reproducible against `requirements-lock.txt`.
4. Resolve port mapping: `deploy/docker/docker-compose.yml:6` exposes `127.0.0.1:8000:8000`, while active runtime uses `18201`/`15274`. Do not change ports in this stabilization.
5. Do not enable the compose `postgres`/`redis` services for V1 without owner decision; V1 was tested against SQLite. `POSTGRES_PASSWORD` has only a placeholder default in compose; supply secrets via owner mechanism if ever enabled.
6. Preserve `read_only: true`, `tmpfs: [/tmp]`, non-root `USER appuser`, and loopback-only publishing in any approved deployment.

## Approved release procedure (future, not executed)

1. Freeze final review commit; record `git rev-parse HEAD`, timestamp, and evidence path.
2. Build an image only after precondition 3 is completed; do not use `latest` as an immutable reference.
3. Start the new backend/frontend on separate temporary ports with a **copy** of the DB; run `/health`, `/v1/health`, `/readyz`, `/v1/control-plane/model-status`, frontend root/proxy, and synthetic `PONG` chat.
4. Require `/readyz` to be `ok` only when knowledge documents and embedding identity are genuinely verified; degraded with `documents=0` is acceptable for smoke, not for release.
5. Run PC PIAK-03 acceptance with approved artifacts; capture golden answer and evidence SHA.
6. Only after owner `GO`, switch traffic to the approved mapping. Stop the previous process only after new-process probes pass. Keep the old process/image stopped but available until post-release observation ends.
7. Re-run active `/health`, frontend root, Ollama version, DB `quick_check`, and admin-boundary negative probes after switch.

## Rollback procedure

1. Stop only the newly started RC frontend/backend processes; do not stop Ollama or unrelated listeners.
2. Restart or repoint to the previous `b44b01e7` artifact on the previously approved ports `18201`/`15274`.
3. Do **not** delete, overwrite, migrate, or restore the DB volume; no schema change exists between `b44b01e7` and the RC.
4. Verify active `/health` HTTP 200 and build identity, frontend root/health 200, Ollama `/api/version` 200, DB `quick_check=ok`/`9` tables, and `documents=0` unchanged.
5. Record rollback command, exit code, timestamp, and SHA. If rollback verification fails, stop and escalate; do not improvise DB changes.

## Evidence index

`g_deploy_facts.*`, `g_release_diff.*`, `g_active_commit.*`, `a_processes.*`, `c_ports_after_isolated.*`, `e_ports_after_stop.*`, `e_db_stat.*`, `e_db_hash.*`, `e_db_pragmas.*`, `e_active_after_stop.*`, `a_readyz_status.*`, `c_readyz_alias.*`, `c_model_status_canonical.*`, `PC_PIAK03_ACCEPTANCE_HANDOFF.md`. Full commands and exit codes: `evidence/commands.tsv`.
