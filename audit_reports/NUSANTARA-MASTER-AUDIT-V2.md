# NUSANTARA AI - MASTER ENGINEERING AUDIT V2

Repository: C:\users\dmaza\mcp-starter

Audit Date: 2026-10-03 13:52:11

Mode: READ-ONLY

## Overall Status

**WARN**

| Metric | Count |
|---|---:|
| PASS | 37 |
| WARN | 669 |
| FAIL | 0 |
| INFO | 8 |

## Findings

| Area | Status | Finding | Evidence | Action |
|---|---|---|---|---|
| Baseline | PASS | Git repository terdeteksi. | .git |  |
| Baseline | PASS | Direktori app tersedia. | app |  |
| Baseline | INFO | Jumlah file Python terdeteksi: 10809 | Recursive Python scan |  |
| Architecture | WARN | Architecture Contract tidak ditemukan pada lokasi kandidat. | Architecture contract candidates | Audit manual nama/lokasi dokumen diperlukan. |
| Core Hardening | PASS | Komponen ditemukan: app\core\hardening\validator.py | app\core\hardening\validator.py |  |
| Core Hardening | PASS | Komponen ditemukan: app\core\hardening\timeout.py | app\core\hardening\timeout.py |  |
| Core Hardening | PASS | Komponen ditemukan: app\core\hardening\retry.py | app\core\hardening\retry.py |  |
| Core Hardening | PASS | Komponen ditemukan: app\core\hardening\circuit_breaker.py | app\core\hardening\circuit_breaker.py |  |
| Core Hardening | PASS | Komponen ditemukan: app\core\hardening\safe_execution.py | app\core\hardening\safe_execution.py |  |
| Core Hardening | PASS | Targeted Phase 2 test ditemukan. | tests\test_phase2_hardening.py |  |
| Observability | PASS | Komponen ditemukan: app\observability\context.py | app\observability\context.py |  |
| Observability | PASS | Komponen ditemukan: app\observability\logging.py | app\observability\logging.py |  |
| Observability | PASS | Komponen ditemukan: app\observability\metrics.py | app\observability\metrics.py |  |
| Observability | PASS | Phase 3 test ditemukan: tests\test_phase3_observability.py | tests\test_phase3_observability.py |  |
| Observability | PASS | Phase 3 test ditemukan: tests\test_phase3_http_integration.py | tests\test_phase3_http_integration.py |  |
| Observability | PASS | Phase 3 test ditemukan: tests\test_phase3_metrics_integration.py | tests\test_phase3_metrics_integration.py |  |
| Governance | PASS | Governance tool registry ditemukan. | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: Risk | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: Decision | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: permission | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: approval | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: audit | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: schema validation | app\governance\tools.py |  |
| Governance | PASS | Governance memiliki indikator: safe execution | app\governance\tools.py |  |
| Approval/Audit | PASS | Direktori tersedia: app\approval | app\approval |  |
| Approval/Audit | INFO | Direktori tidak ditemukan: app\audit | app\audit | Pastikan fungsi approval/audit tetap memiliki single source of truth. |
| Approval/Audit | PASS | Direktori tersedia: app\observability | app\observability |  |
| Memory | PASS | Memory layer ditemukan: app\memory | app\memory |  |
| RAG | PASS | RAG layer ditemukan: app\rag | app\rag |  |
| MCP | PASS | MCP layer ditemukan: app\mcp | app\mcp |  |
| Security | PASS | Security-related layer ditemukan: app\security | app\security |  |
| Security | PASS | Security-related layer ditemukan: app\governance | app\governance |  |
| Security | PASS | Security-related layer ditemukan: app\core\hardening | app\core\hardening |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_graph_adapter_20261002_132323.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_graph_rag_production_20261002_142501.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_graph_rag_v2_20261002_132824.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_production_rag_20261002_141904.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_prod_integration_20261002_142101.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_quality_20261002_131836.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_safe_graph_rag_20261002_142601.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_source_cleanup_20261002_142345.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | developer_core_engine.before_source_filter_20261002_132632.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara_master_pdf_sop_engine.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | ocr_test_capil02.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | ocr_test_capil02_ind.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | sop_governance_ocr_engine.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: test_provider.py | C:\users\dmaza\mcp-starter\test_provider.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\typing_extensions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\typing_extensions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\anyio\to_interpreter.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\anyio\to_process.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\anyio\abc\_subprocesses.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\anyio\streams\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\anyio\_backends\_asyncio.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\anyio\_backends\_asyncio.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: shell=True | .venv\Lib\site-packages\anyio\_backends\_trio.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\anyio\_backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\anyio\_core\_subprocesses.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\anyio\_core\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\click\shell_completion.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\click\_termui_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\fastapi\dependencies\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\fastapi\openapi\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\httpcore\_backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\build_env\installer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\cli\main.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\cli\main_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: shell=True | .venv\Lib\site-packages\pip\_internal\commands\configuration.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\commands\configuration.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\network\auth.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\network\session.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_internal\operations\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_internal\operations\build\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_internal\resolution\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_internal\resolution\legacy\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_internal\resolution\resolvelib\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_internal\utils\subprocess.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_internal\utils\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\pip\_vendor\distlib\scripts.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_vendor\distlib\util.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_vendor\distro\distro.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_vendor\packaging\tags.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_vendor\packaging\_musllinux.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pip\_vendor\packaging\_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\pip\_vendor\pkg_resources\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\pip\_vendor\pygments\lexers\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pip\_vendor\pyproject_hooks\_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pip\_vendor\rich\markup.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pip\_vendor\urllib3\contrib\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\json_schema.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\validate_call_decorator.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pydantic\deprecated\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\v1\utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_decorators.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_fields.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_generate_schema.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\pydantic\_internal\_git.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_namespace_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_signature.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_typing_extra.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\pydantic\_internal\_typing_extra.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | .venv\Lib\site-packages\pydantic\_internal\_validate_call.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\pydantic\_internal\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | .venv\Lib\site-packages\typing_inspection\typing_objects.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\typing_inspection\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\uvicorn\_subprocess.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\uvicorn\lifespan\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\uvicorn\loops\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\uvicorn\middleware\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\uvicorn\protocols\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\uvicorn\protocols\http\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\uvicorn\protocols\websockets\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\watchfiles\run.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: os.system( | .venv\Lib\site-packages\websockets\cli.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | .venv\Lib\site-packages\websockets\version.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\websockets\asyncio\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\websockets\sync\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\.venv\Lib\site-packages\websockets\trio\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | app\governance\sandbox.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\app\improvement\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | app\knowledge\production_embedding_bridge.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: normalizer_safe.py | C:\users\dmaza\mcp-starter\app\language\normalizer_safe.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | app\language\semantic\indobert_client.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\app\language\semantic\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\app\research\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\app\security\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\app\tools\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\indobert_bridge.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\indobert_worker.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\test_indobert_worker.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\typing_extensions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\typing_extensions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\launchers.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\optimizer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\commands\env.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\commands\launch.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\commands\tpu.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\test_utils\testing.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\accelerate\test_utils\testing.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\test_utils\scripts\external_deps\test_checkpointing.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\test_utils\scripts\external_deps\test_ds_multiple_model.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\test_utils\scripts\external_deps\test_metrics.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\test_utils\scripts\external_deps\test_performance.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\utils\environment.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\utils\launch.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\utils\launch.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\accelerate\utils\megatron_lm.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\accelerate\utils\torch_xla.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\anyio\to_interpreter.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\anyio\to_process.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\anyio\abc\_subprocesses.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\anyio\streams\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\anyio\_backends\_asyncio.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\anyio\_backends\_asyncio.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: shell=True | nusantara-models\.venv\Lib\site-packages\anyio\_backends\_trio.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\anyio\_backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\anyio\_core\_subprocesses.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\anyio\_core\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\click\shell_completion.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\click\_termui_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\filelock\_api.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\fsspec\conftest.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\fsspec\gui.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\fsspec\implementations\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\functorch\dim\magic_trace.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\functorch\einops\rearrange.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\functorch\_src\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\httpcore\_backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\huggingface_hub\hub_mixin.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\_dataset_viewer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\_login.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: shell=True | nusantara-models\.venv\Lib\site-packages\huggingface_hub\_sandbox.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\extensions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\extensions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\lfs.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\sandbox.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\spaces.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\system.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\cli\_cli_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\huggingface_hub\inference\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\huggingface_hub\inference\_generated\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\inference\_mcp\_cli_hacks.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\huggingface_hub\inference\_mcp\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\huggingface_hub\utils\tqdm.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\utils\_git_credential.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\huggingface_hub\utils\_subprocess.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\jinja2\debug.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\jinja2\environment.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\jinja2\lexer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\jinja2\nativetypes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\jinja2\nodes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\markdown_it\cli\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\markdown_it\common\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\mpmath\identification.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\mpmath\libmp\backend.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\networkx\conftest.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\networkx\algorithms\bipartite\edgelist.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\networkx\readwrite\edgelist.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\networkx\readwrite\gml.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\networkx\readwrite\multiline_adjlist.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\networkx\utils\decorators.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\numpy\conftest.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\f2py\auxfuncs.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\f2py\capi_maps.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\f2py\crackfortran.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\numpy\f2py\_backends\_meson.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\lib\_format_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\lib\_npyio_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\polynomial\hermite_e.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\numpy\testing\_private\utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\numpy\testing\_private\utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\numpy\testing\_private\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\_core\arrayprint.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\numpy\_core\_internal.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\numpy\_pyinstaller\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\packaging\tags.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\packaging\_musllinux.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\packaging\_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\build_env\installer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\cli\main.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\cli\main_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: shell=True | nusantara-models\.venv\Lib\site-packages\pip\_internal\commands\configuration.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\commands\configuration.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\network\auth.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\network\session.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_internal\operations\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_internal\operations\build\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_internal\resolution\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_internal\resolution\legacy\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_internal\resolution\resolvelib\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_internal\utils\subprocess.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_internal\utils\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\distlib\scripts.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_vendor\distlib\util.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_vendor\distro\distro.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_vendor\packaging\tags.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_vendor\packaging\_musllinux.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\packaging\_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\pkg_resources\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\pygments\lexers\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pip\_vendor\pyproject_hooks\_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\pip\_vendor\rich\markup.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\pip\_vendor\urllib3\contrib\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\psutil\_psaix.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\psutil\_pssunos.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\psutil\_pswindows.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\psutil\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pygments\formatters\img.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\pygments\formatters\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\pygments\formatters\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\pygments\lexers\special.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\pygments\lexers\_julia_builtins.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\pygments\lexers\_scilab_builtins.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\pygments\lexers\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\rich\markup.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\setuptools\build_meta.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\installer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\setuptools\launch.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\setuptools\wheel.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_scripts.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\command\develop.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\setuptools\compat\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\setuptools\config\expand.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\core.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\spawn.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\util.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\command\bdist_rpm.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\command\_framework_compat.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\compilers\C\base.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\compilers\C\base.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\compilers\C\cygwin.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\compilers\C\msvc.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\compilers\C\unix.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_distutils\compilers\C\zos.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\backports\tarfile\compat\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\importlib_metadata\compat\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\jaraco\context\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\jaraco\functools\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\more_itertools\recipes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\packaging\tags.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\packaging\_musllinux.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\packaging\_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\setuptools\_vendor\zipp\compat\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\shellingham\posix\ps.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\abc.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\assumptions\assume.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\assumptions\wrapper.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\assumptions\relation\binrel.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\assumptions\relation\equality.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\benchmarks\bench_meijerint.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\codegen\algorithms.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\codegen\algorithms.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\codegen\ast.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\codegen\cfunctions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\combinatorics\schur_number.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\core\function.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\core\mod.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\core\symbol.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\core\sympify.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\core\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\external\importtools.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\combinatorial\factorials.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\combinatorial\numbers.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\complexes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\exponential.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\hyperbolic.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\integers.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\miscellaneous.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\piecewise.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\trigonometric.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\functions\elementary\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\bessel.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\beta_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\delta_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\elliptic_integrals.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\error_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\gamma_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\hyper.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\mathieu_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\polynomials.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\singularity_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\spherical_harmonics.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\tensor_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\functions\special\zeta_functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\functions\special\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\integrals\manualintegrate.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\integrals\meijerint.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\integrals\prde.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\integrals\rde.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\integrals\risch.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\integrals\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\interactive\session.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\logic\boolalg.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\logic\algorithms\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\matrices\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\parsing\ast_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\parsing\ast_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\parsing\sympy_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\parsing\sympy_parser.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\parsing\autolev\_build_autolev_antlr.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\parsing\latex\_build_latex_antlr.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\secondquant.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\biomechanics\curve.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\control\control_plots.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\physics\hep\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\quantum\anticommutator.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\quantum\commutator.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\quantum\hilbert.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\physics\quantum\state.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\plotting\experimental_lambdify.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\plotting\series.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\plotting\backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\plotting\pygletplot\plot_axes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\plotting\pygletplot\plot_interval.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\appellseqs.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\compatibility.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\densetools.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\euclidtools.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\galoistools.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\polys\monomials.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\polyclasses.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\polyconfig.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\polyquinticconst.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\polyroots.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\polytools.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\ring_series.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\rootisolation.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\rootoftools.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\polys\benchmarks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\numberfields\galoisgroups.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\numberfields\galois_resolvents.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\polys\numberfields\subfield.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\printing\dot.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\printing\gtk.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\printing\preview.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\printing\python.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\printing\repr.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\series\formal.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\series\benchmarks\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\sets\handlers\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\simplify\gammasimp.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\solvers\polysys.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\solvers\benchmarks\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\stats\sampling\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\tensor\tensor.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\testing\runtests.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\testing\runtests.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\utilities\lambdify.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\utilities\lambdify.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\sympy\utilities\matchpy_connector.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\sympy\utilities\matchpy_connector.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\sympy\utilities\mathml\data\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\utilities\_compilation\compilation.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: shell=True | nusantara-models\.venv\Lib\site-packages\sympy\utilities\_compilation\runners.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\sympy\utilities\_compilation\runners.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_guards.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_precompile.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_precompile.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: _thread_safe_fork.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_thread_safe_fork.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\amp\autocast_mode.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\nn\quantizable\modules\activation.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\nn\quantizable\modules\rnn.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\ns\_numeric_suite_fx.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\ns\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\ns\fx\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\scheduler\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\sparsifier\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\_experimental\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\_experimental\activation_sparsifier\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\_experimental\data_sparsifier\lightning\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\_experimental\data_sparsifier\lightning\callbacks\data_sparsity.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\pruning\_experimental\data_sparsifier\lightning\callbacks\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\fuser_method_mappings.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\fuse_modules.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\quantize.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\quantize_fx.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\quantize_jit.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\backend_config\onednn.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\ao\quantization\fx\_model_report\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\autograd\grad_mode.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\backends\xeon\run_cpu.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\backends\xeon\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\backends\_coreml\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\backends\_nnapi\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\contrib\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\cuda\graphs.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\cuda\_graph_annotations.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\cuda\_memory_viz.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\cuda\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\algorithms\model_averaging\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\algorithms\_checkpoint\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\algorithms\_quantization\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\distributed\checkpoint\_experimental\builder.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\distributed\checkpoint\_experimental\checkpoint_process.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\elastic\agent\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\distributed\elastic\multiprocessing\api.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: os.system( | nusantara-models\.venv\Lib\site-packages\torch\distributed\elastic\multiprocessing\redirects.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\distributed\elastic\multiprocessing\subprocess_handler\subprocess_handler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\distributed\elastic\rendezvous\etcd_server.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\flight_recorder\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\distributed\flight_recorder\components\builder.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\flight_recorder\components\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\distributed\fsdp\_flat_param.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\distributed\fsdp\_runtime_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\distributed\nn\api\remote_module.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\nn\api\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\distributed\nn\jit\instantiator.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\nn\jit\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\nn\jit\templates\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\distributed\pipelining\schedules.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\distributed\_shard\sharding_spec\chunk_sharding_spec_ops\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\distributed\_symmetric_memory\_nvshmem_triton.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\export\exported_program.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\export\_unlift.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\fx\graph.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\fx\graph_module.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\fx\operator_schemas.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\fx\experimental\optimization.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\fx\experimental\proxy_tensor.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\fx\experimental\rewriter.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\fx\experimental\symbolic_shapes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\fx\experimental\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\fx\experimental\migrate_gradual_types\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\fx\passes\splitter_base.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\fx\passes\backends\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\fx\passes\dialect\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\fx\passes\dialect\common\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\jit\annotations.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\jit\frontend.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\jit\unsupported_tensor_ops.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\jit\_freeze.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\jit\_trace.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\jit\_passes\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\mtia\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\nativert\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\nativert\backends\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\nested\_internal\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\nn\backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\nn\modules\activation.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\nn\modules\batchnorm.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\nn\modules\module.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\nn\modules\transformer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\nn\utils\fusion.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\numa\binding.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\numa\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\exporter\_building.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\exporter\_compat.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\exporter\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\exporter\_torchlib\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\fx\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\torchscript_exporter\verification.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\onnx\_internal\torchscript_exporter\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\package\package_importer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\common_distributed.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\common_fsdp.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\common_modules.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\common_quantization.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\common_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\jit_metaprogramming_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\jit_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\distributed_test.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\nn\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\nn\api\remote_module_test.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\nn\api\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\rpc\dist_autograd_test.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\rpc\rpc_test.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\rpc\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\rpc\examples\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\rpc\jit\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\_shard\sharded_tensor\_test_ops_common.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\distributed\_tensor\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\generated\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\testing\_internal\test_module\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\collect_env.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\cpp_extension.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\utils\mobile_optimizer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\_get_clean_triton.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\utils\_traceback.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\benchmark\examples\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\benchmark\op_fuzzers\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\benchmark\utils\timer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\benchmark\utils\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\benchmark\utils\valgrind_wrapper\timer_interface.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\benchmark\utils\valgrind_wrapper\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\data\dataloader.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\data\datapipes\utils\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\jit\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\utils\tensorboard\_pytorch_graph.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\viz\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\utils\_strobelight\cli_function_profiler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\_strobelight\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\utils\_sympy\functions.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\utils\_sympy\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\xpu\graphs.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\xpu\__init__.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_custom_op\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_dispatch\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\bytecode_debugger.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\bytecode_debugger.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\convert_frame.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\convert_frame.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\debug_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\dynamo_profiler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\functional_export.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\guards.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\guards.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\package.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\test_minifier_common.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\test_minifier_common.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\backends\torchxla.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_dynamo\backends\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\repro\after_aot.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\repro\after_aot.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\repro\after_dynamo.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\variables\builtin.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_dynamo\variables\tensor.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_export\pass_infra\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_export\serde\serialize.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_export\serde\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_functorch\compilers.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_functorch\_aot_autograd\codegen.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_higher_order_ops\invoke_leaf_function.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_higher_order_ops\triton_kernel_wrap.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_higher_order_ops\passes\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\async_compile.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\autotune_process.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\cache.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\codecache.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\comm_analysis.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\comm_analysis.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\compiler_bisector.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\compiler_bisector.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\compile_fx_ext.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\cpp_builder.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\cpu_vec_isa.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\ops_handler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\profiler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\rocm_multiarch_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\select_algorithm.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\standalone_compile.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\wrapper_benchmark.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\analysis\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\autoheuristic\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\autoheuristic\artifacts\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\cpp_wrapper_cpu.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\wrapper.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\cuda\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\cutlass\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\cutlass\lib_extensions\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\cutlass\lib_extensions\cutlass_mock_imports\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\mtia\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\rocm\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\xpu\compile_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\codegen\xpu\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_inductor\compile_worker\subproc_pool.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\compile_worker\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\fx_passes\efficient_conv_bn_eval.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\fx_passes\pre_grad.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\fx_passes\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\fx_passes\serialized_patterns\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\kernel\flex\flex_flash_attention.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\kernel\flex_gemm\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\kernel\vendored_templates\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\kernel\vendored_templates\cutedsl\kernels\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\kernel\vendored_templates\cutedsl\wrappers\dense_blockscaled_gemm_kernel.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\runtime\compile_tasks.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\runtime\triton_heuristics.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_inductor\runtime\triton_lazy_compile.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_inductor\runtime\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\torch\_library\infer_schema.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_strobelight\cli_function_profiler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_strobelight\compile_time_profiler.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_strobelight\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_vendor\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_vendor\quack\autotuner.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torch\_vendor\quack\_compile_worker.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torch\_vendor\quack\bench\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torchgen\aoti\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torchgen\api\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torchgen\operator_versions\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torchgen\packaged\autograd\__init__.py |  |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torchgen\selective_build\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\torchgen\static_runtime\gen_static_runtime_ops.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Tidak dapat membaca file: __init__.py | C:\users\dmaza\mcp-starter\nusantara-models\.venv\Lib\site-packages\torchgen\static_runtime\__init__.py |  |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\tqdm\cli.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\modeling_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\transformers\testing_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: exec( | nusantara-models\.venv\Lib\site-packages\transformers\testing_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\trainer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\transformers\cli\add_new_model_like.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\data\metrics\squad_metrics.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\generation\continuous_batching\continuous_api.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\integrations\executorch.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\integrations\flex_attention.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\integrations\peft.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\auto\auto_factory.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\bigbird_pegasus\modeling_bigbird_pegasus.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\big_bird\modeling_big_bird.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\blip\modeling_blip.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\blip_2\modeling_blip_2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\blt\modeling_blt.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\blt\modular_blt.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\bridgetower\modeling_bridgetower.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\chameleon\modeling_chameleon.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colmodernvbert\configuration_colmodernvbert.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colmodernvbert\modeling_colmodernvbert.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colmodernvbert\modular_colmodernvbert.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colmodernvbert\processing_colmodernvbert.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colpali\configuration_colpali.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colpali\modeling_colpali.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colpali\modular_colpali.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colpali\processing_colpali.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colqwen2\configuration_colqwen2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colqwen2\modeling_colqwen2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colqwen2\modular_colqwen2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\colqwen2\processing_colqwen2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\decision_transformer\modeling_decision_transformer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\emu3\modeling_emu3.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\emu3\modular_emu3.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\encoder_decoder\modeling_encoder_decoder.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\esmfold2\modeling_esmfold2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\esmfold2\modular_esmfold2.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\glm_image\modeling_glm_image.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\higgs_audio_v2_tokenizer\modeling_higgs_audio_v2_tokenizer.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\janus\modeling_janus.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\musicgen\modeling_musicgen.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\musicgen_melody\modeling_musicgen_melody.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\neomme\modeling_neomme.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\neomme\modular_neomme.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\rag\modeling_rag.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\rag\retrieval_rag.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\sam3_video\modeling_sam3_video.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\speech_encoder_decoder\modeling_speech_encoder_decoder.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\timm_wrapper\modeling_timm_wrapper.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\vilt\modeling_vilt.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\vision_encoder_decoder\modeling_vision_encoder_decoder.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: eval( | nusantara-models\.venv\Lib\site-packages\transformers\models\xcodec\modeling_xcodec.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\transformers\pipelines\audio_classification.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\transformers\pipelines\audio_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\transformers\utils\import_utils.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\typer\main.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\typer\_completion_classes.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\typer\_completion_shared.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | nusantara-models\.venv\Lib\site-packages\typer\_click\_termui_impl.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | scripts\production_indobert_hardening.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | scripts\production_kb_hardening.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Security | WARN | Pattern sensitif terdeteksi: subprocess. | scripts\release_check.py | Audit konteks manual diperlukan; tidak otomatis berarti vulnerability. |
| Testing | INFO | Jumlah file test Python: 13 | tests |  |
| Testing | WARN | Duplicate test basename: test_evaluation.py | tests | Gunakan pytest --import-mode=importlib bila diperlukan. |
| Build/Test Configuration | PASS | pyproject.toml ditemukan. | pyproject.toml |  |
| Build/Test Configuration | PASS | Konfigurasi pytest terdeteksi. | pyproject.toml |  |
| Git | INFO | Working tree memiliki perubahan. | git status --short | Audit perubahan sebelum release. |
| Targeted Testing | PASS | Test berhasil: tests\test_phase2_hardening.py | ============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\users\dmaza\mcp-starter
configfile: pyproject.toml
plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 10 items

tests\test_phase2_hardening.py ..........                                [100%]

============================= 10 passed in 0.61s ============================== |  |
| Targeted Testing | PASS | Test berhasil: tests\test_phase3_observability.py | ============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\users\dmaza\mcp-starter
configfile: pyproject.toml
plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 10 items

tests\test_phase3_observability.py ..........                            [100%]

============================= 10 passed in 0.03s ============================== |  |
| Targeted Testing | PASS | Test berhasil: tests\test_phase3_http_integration.py | ============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\users\dmaza\mcp-starter
configfile: pyproject.toml
plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2 items

tests\test_phase3_http_integration.py ..                                 [100%]

============================== warnings summary ===============================
..\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\dmaza\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

..\AppData\Local\Programs\Python\Python313\Lib\site-packages\starlette\testclient.py:53
  C:\Users\dmaza\AppData\Local\Programs\Python\Python313\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 0.41s ======================== |  |
| Targeted Testing | PASS | Test berhasil: tests\test_phase3_metrics_integration.py | ============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\users\dmaza\mcp-starter
configfile: pyproject.toml
plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 3 items

tests\test_phase3_metrics_integration.py ...                             [100%]

============================== warnings summary ===============================
..\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\dmaza\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

..\AppData\Local\Programs\Python\Python313\Lib\site-packages\starlette\testclient.py:53
  C:\Users\dmaza\AppData\Local\Programs\Python\Python313\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 3 passed, 2 warnings in 0.35s ======================== |  |
| Full Regression | PASS | Full pytest regression berhasil. | ============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\users\dmaza\mcp-starter
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 126 items

tests\evaluation\test_smoke.py .....                                     [  3%]
tests\test_language_normalizer.py ..............                         [ 15%]
tests\test_phase2_hardening.py ..........                                [ 23%]
tests\test_phase3_http_integration.py ..                                 [ 24%]
tests\test_phase3_metrics_integration.py ...                             [ 26%]
tests\test_phase3_observability.py ..........                            [ 34%]
tests\v2\test_devcore.py ..s...........                                  [ 46%]
tests\v2\test_devcore_integration.py ......                              [ 50%]
tests\v2\test_devcore_routes.py ......                                   [ 55%]
tests\v2\test_phases_7_21.py ...............................             [ 80%]
tests\v2\test_v2_core.py .........................                       [100%]

============================== warnings summary ===============================
..\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\dmaza\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

..\AppData\Local\Programs\Python\Python313\Lib\site-packages\starlette\testclient.py:53
  C:\Users\dmaza\AppData\Local\Programs\Python\Python313\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

tests/evaluation/test_smoke.py::test_mcp_handoff
  C:\Users\dmaza\mcp-starter\app\handoff\engine.py:51: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    created_at=datetime.utcnow().isoformat(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================= 125 passed, 1 skipped, 3 warnings in 14.35s ================= |  |
| Phase Assessment | INFO | Phase 0 Baseline: READY |  |  |
| Phase Assessment | INFO | Phase 1 Architecture: DOCUMENT NOT CONFIRMED |  |  |
| Phase Assessment | INFO | Phase 2 Hardening: TARGETED TEST PASS |  |  |
| Phase Assessment | INFO | Phase 3 Observability: TARGETED TESTS PASS |  |  |

## Engineering Rule

A phase is not FINAL merely because source files exist.

Expected evidence:

IMPLEMENTATION + TARGETED TEST + SECURITY + FULL REGRESSION + EVIDENCE

This audit does not modify production source code.

Findings must be analyzed before implementation changes are made.
