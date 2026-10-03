from pathlib import Path

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8")

old = "from app.core.gate_integration import GateIntegration"
new = """from app.core.gate_integration import GateIntegration
from app.developer_core.graph_bridge import GraphifyBridge"""

if "from app.developer_core.graph_bridge import GraphifyBridge" not in s:
    if old not in s:
        raise SystemExit("Import GateIntegration tidak ditemukan.")
    s = s.replace(old, new, 1)

old = "_gate_integration = GateIntegration()"
new = """_gate_integration = GateIntegration()
_developer_core = GraphifyBridge()"""

if "_developer_core = GraphifyBridge()" not in s:
    if old not in s:
        raise SystemExit("Instance GateIntegration tidak ditemukan.")
    s = s.replace(old, new, 1)

marker = "        return {"

if "developer_runtime = _developer_core.runtime_snapshot(" not in s:
    pos = s.find(marker)

    # Cari return terakhir di function chat.
    pos = s.rfind(marker)

    if pos == -1:
        raise SystemExit("Final return tidak ditemukan.")

    block = """        developer_runtime = _developer_core.runtime_snapshot(
            session_id=request.session_id,
            user_input=request.user_input,
            gate_pipeline=gate_context,
            provider_status=model_status,
            latency_ms=latency_ms,
            grounded=bool(
                gate_context
                .get("reasoning", {})
                .get("status") == "grounded"
            ),
        )

"""

    s = s[:pos] + block + s[pos:]

    # Masukkan field setelah return {
    insert = '            "developer_core": developer_runtime,\n'

    return_pos = s.find(marker, pos)

    if return_pos == -1:
        raise SystemExit("Return insertion point tidak ditemukan.")

    after = return_pos + len(marker)

    s = s[:after] + "\n" + insert + s[after:]

compile(s, str(p), "exec")
p.write_text(s, encoding="utf-8")

print("GATE 14 RUNTIME ROUTES PATCH : PASS")
print("SYNTAX                       : OK")
