# NUSANTARA DEEP RUNTIME AUDIT

Generated: 2026-10-05 14:56:05
Repository: C:\users\dmaza\mcp-starter

## IMPORTANT

This report is evidence-based but does not automatically declare a phase COMPLETE merely because source files exist.

## Summary

| Metric | Value |
|---|---:|
| Evidence Checks | 35 |
| PASS / FOUND | 30 |
| FAIL | 0 |
| PARTIAL | 0 |
| NOT VERIFIED / NOT FOUND | 3 |
| Evidence Confidence | 85.71% |

## Evidence

| Phase | Area | Status | Evidence |
|---|---|---|---|
| ENV | Python | PASS | Python 3.13.15 |
| 0-1 | PATH:app | PASS | Exists |
| 0-1 | PATH:tests | PASS | Exists |
| 0-1 | PATH:scripts | PASS | Exists |
| 0-1 | PATH:docs | PASS | Exists |
| 0-1 | PATH:app\main.py | PASS | Exists |
| 0-1 | PATH:app\knowledge | PASS | Exists |
| 0-1 | PATH:app\core | PASS | Exists |
| 0-1 | PATH:app\developer_core | PASS | Exists |
| 0 | Git Branch | INFO | master |
| 0 | Git Status | INFO | M app/developer_core/approval_controller.py   M app/developer_core/claude_code_integration.py   M app/developer_core/context_router.py   M app/developer_core/engine.py   M app/knowledge/production_embedding_bridge.py   M scripts/validate_gate14_runtime_graph.py   M scripts/validate_gate16_audit.py  ?? "NUSANTARA MASTER DEVELOPER.md"  ?? app/runtime/  ?? config/  ?? docs/audit/BASELINE.md  ?? docs/audit/MARKITDOWN_AUDIT.md  ?? docs/audit/MASTER_ENGINEERING_AUDIT.md  ?? docs/audit/NUSANTARA_AUDIT_PHASE_0_21.md  ?? docs/audit/RAG_SCHEMA_AUDIT.md  ?? docs/audit/SECURITY_TRACE.md  ?? scripts/audit_all_phases.ps1  ?? scripts/audit_deep.ps1  ?? scripts/baseline_rag_cache.py  ?? scripts/install_rag_cache.ps1  ?? scripts/validate_gate17_4.py  ?? tests/test_v1_smoke.py |
| 20 | Python Compile | PASS | compileall completed successfully |
| 20 | Pytest | PASS | ============================= test session starts =============================  platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0  rootdir: C:\users\dmaza\mcp-starter  configfile: pyproject.toml  testpaths: tests  plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function  collected 148 items    tests\evaluation\test_smoke.py .....                                     [  3%]  tests\test_gate14_developer_core.py .....                                [  6%]  tests\test_gate14_mapper_impact.py .....                                 [ 10%]  tests\test_gate_integration.py ...                                       [ 12%]  tests\test_gates_8_16.py ......                          ... |
| 2 | Core Hardening | PASS | ============================= test session starts =============================  platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0  rootdir: C:\users\dmaza\mcp-starter  configfile: pyproject.toml  plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function  collected 10 items    tests\test_phase2_hardening.py ..........                                [100%]    ============================= 10 passed in 0.59s ============================== |
| 3 | Observability | PASS | ============================= test session starts =============================  platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0  rootdir: C:\users\dmaza\mcp-starter  configfile: pyproject.toml  plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function  collected 15 items    tests\test_phase3_http_integration.py ..                                 [ 13%]  tests\test_phase3_metrics_integration.py ...                             [ 33%]  tests\test_phase3_observability.py ..........                            [100%]    ============================== warnings summary ===============================  ..\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testc... |
| 4 | Trust | FOUND | Keyword/component detected in app source |
| 5 | Policy | FOUND | Keyword/component detected in app source |
| 6 | Memory | FOUND | Keyword/component detected in app source |
| 7 | RAG | FOUND | Keyword/component detected in app source |
| 8 | MCP | FOUND | Keyword/component detected in app source |
| 9 | Tool Governance | NOT FOUND | No matching component detected |
| 10 | Experience | FOUND | Keyword/component detected in app source |
| 11 | Feedback | FOUND | Keyword/component detected in app source |
| 12 | Evaluation | FOUND | Keyword/component detected in app source |
| 13 | Failure Analysis | FOUND | Keyword/component detected in app source |
| 14 | Gap Detection | FOUND | Keyword/component detected in app source |
| 15 | Knowledge Discovery | NOT FOUND | No matching component detected |
| 16 | Experiment | FOUND | Keyword/component detected in app source |
| 17 | Developer Core | FOUND | Keyword/component detected in app source |
| 18 | Human Approval | FOUND | Keyword/component detected in app source |
| 17 | Hermes | FOUND | Hermes references detected |
| 17 | Graphify | FOUND | Graphify references detected; connection still requires runtime verification |
| 17 | DeveloperCore.self_analyze | PASS | {"developer_core": {"version": "14.0.0-graphify-native", "status": "ready"}, "graphify": {"path": "graphify-out\\graph.json", "loaded": true, "nodes": 2824, "edges": 5920}, "gates": {"8": {"name": "Reasoning Engine", "status": "known"}, "9": {"name": "Decision / Policy Engine", "status": "known"}, "10": {"name": "Memory / Context Engine", "status": "known"}, "11": {"name": "Tool / Action Engine", "status": "known"}, "12": {"name": "Existing Tools", "status": "known"}, "13": {"name": "Workflow / Orchestration", "status": "known"}, "14": {"name": "Developer Core / Graph", "status": "known"}}, "engines": [{"name": "Language Engine", "path": "app/language", "exists": true, "python_files": 12, "status": "active"}, {"name": "Problem Engine", "path": "app/problem", "exists": true, "python_files":... |
| 3 | FastAPI /health | PASS | {"status":"ok","version":"0.1.0"} |
| 1 | FastAPI /v1 | NOT VERIFIED | Endpoint unavailable or route requires another method |

## Interpretation

PASS means the corresponding runtime/static evidence succeeded.

FOUND means the component appears in source code but does NOT prove integration.

PARTIAL means some evidence exists but completion criteria are not proven.

NOT VERIFIED means the audit could not establish runtime evidence.

FAIL means an executable check failed.

## Recommended Next Action

Do not implement new features based only on this report.

Use failed and NOT VERIFIED evidence to determine the next engineering task.

V1 remains the primary scope until its gates are satisfied.
