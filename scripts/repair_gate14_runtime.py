from pathlib import Path
import ast

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8")

# ------------------------------------------------------------
# 1. Pastikan import Developer Core
# ------------------------------------------------------------
imp = "from app.developer_core.graph_bridge import GraphifyBridge"

if imp not in s:
    anchor = "from app.core.gate_integration import GateIntegration"
    if anchor not in s:
        raise SystemExit("Anchor GateIntegration tidak ditemukan.")
    s = s.replace(anchor, anchor + "\n" + imp, 1)

# ------------------------------------------------------------
# 2. Pastikan singleton Developer Core
# ------------------------------------------------------------
instance = "_developer_core = GraphifyBridge()"

if instance not in s:
    anchor = "_gate_integration = GateIntegration()"
    if anchor not in s:
        raise SystemExit("Instance GateIntegration tidak ditemukan.")
    s = s.replace(anchor, anchor + "\n" + instance, 1)

# ------------------------------------------------------------
# 3. Parse AST untuk menemukan function chat()
# ------------------------------------------------------------
tree = ast.parse(s)

chat_node = None

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "chat":
            chat_node = node
            break

if chat_node is None:
    raise SystemExit("Function chat() tidak ditemukan.")

chat_start = chat_node.lineno
chat_end = chat_node.end_lineno

lines = s.splitlines()

# Python AST line numbers 1-based.
chat_lines = lines[chat_start - 1:chat_end]

# Cari return terakhir di dalam chat().
local_tree = ast.parse("\n".join(chat_lines))

returns = [
    n for n in ast.walk(local_tree)
    if isinstance(n, ast.Return)
]

if not returns:
    raise SystemExit("Return di chat() tidak ditemukan.")

final_return = max(returns, key=lambda n: n.lineno)

# ------------------------------------------------------------
# 4. Ambil posisi absolut final return
# ------------------------------------------------------------
return_abs_line = chat_start + final_return.lineno - 1

# Cari indentation return.
return_line = lines[return_abs_line - 1]
indent = return_line[:len(return_line) - len(return_line.lstrip())]

# ------------------------------------------------------------
# 5. Pastikan developer_runtime dibuat tepat sebelum return
# ------------------------------------------------------------
runtime_marker = "developer_runtime = _developer_core.runtime_snapshot("

# Hapus blok developer_runtime lama DI DALAM chat jika ada.
# Dilakukan berdasarkan rentang baris sederhana sampai penutup blok
# sebelum return, tanpa menyentuh bagian lain.
chat_text = "\n".join(chat_lines)

if runtime_marker in chat_text:
    # Cari baris awal relatif terhadap chat.
    start_rel = None
    for i, line in enumerate(chat_lines):
        if runtime_marker in line:
            start_rel = i
            break

    if start_rel is not None:
        # Hapus sampai baris kosong setelah blok.
        end_rel = start_rel
        while end_rel < len(chat_lines):
            if end_rel > start_rel and chat_lines[end_rel].strip() == "":
                break
            end_rel += 1

        del lines[
            chat_start - 1 + start_rel:
            chat_start - 1 + end_rel
        ]

        # Reparse setelah penghapusan.
        s = "\n".join(lines) + "\n"
        tree = ast.parse(s)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "chat":
                chat_node = node
                break

        chat_start = chat_node.lineno
        chat_end = chat_node.end_lineno
        lines = s.splitlines()
        chat_lines = lines[chat_start - 1:chat_end]

        local_tree = ast.parse("\n".join(chat_lines))
        returns = [
            n for n in ast.walk(local_tree)
            if isinstance(n, ast.Return)
        ]

        final_return = max(returns, key=lambda n: n.lineno)
        return_abs_line = chat_start + final_return.lineno - 1
        return_line = lines[return_abs_line - 1]
        indent = return_line[:len(return_line) - len(return_line.lstrip())]

# ------------------------------------------------------------
# 6. Masukkan runtime snapshot tepat sebelum final return
# ------------------------------------------------------------
runtime_block = [
    f"{indent}# ==============================================================",
    f"{indent}# GATE 14 - DEVELOPER CORE RUNTIME SNAPSHOT",
    f"{indent}# ==============================================================",
    f"{indent}developer_runtime = _developer_core.runtime_snapshot(",
    f"{indent}    session_id=request.session_id,",
    f"{indent}    user_input=request.user_input,",
    f"{indent}    gate_pipeline=gate_context,",
    f"{indent}    provider_status=model_status,",
    f"{indent}    latency_ms=latency_ms,",
    f"{indent}    grounded=bool(",
    f"{indent}        gate_context",
    f"{indent}        .get(\"reasoning\", {{}})",
    f"{indent}        .get(\"status\") == \"grounded\"",
    f"{indent}    ),",
    f"{indent})",
    "",
]

lines[return_abs_line - 1:return_abs_line - 1] = runtime_block

# ------------------------------------------------------------
# 7. Cari lagi final return setelah insertion
# ------------------------------------------------------------
s = "\n".join(lines) + "\n"
tree = ast.parse(s)

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "chat":
        chat_node = node
        break

chat_start = chat_node.lineno
chat_end = chat_node.end_lineno
lines = s.splitlines()
chat_lines = lines[chat_start - 1:chat_end]

local_tree = ast.parse("\n".join(chat_lines))
returns = [
    n for n in ast.walk(local_tree)
    if isinstance(n, ast.Return)
]

final_return = max(returns, key=lambda n: n.lineno)
return_abs_line = chat_start + final_return.lineno - 1

# ------------------------------------------------------------
# 8. Pastikan return dictionary memiliki developer_core
# ------------------------------------------------------------
return_line_index = return_abs_line - 1

# Cari sampai akhir dictionary return.
depth = 0
end_idx = None

for i in range(return_line_index, len(lines)):
    line = lines[i]

    depth += line.count("{")
    depth -= line.count("}")

    if i > return_line_index and depth <= 0:
        end_idx = i
        break

if end_idx is None:
    raise SystemExit("Akhir return dictionary tidak ditemukan.")

return_block = "\n".join(lines[return_line_index:end_idx + 1])

if '"developer_core": developer_runtime' not in return_block:
    # Cari baris return { lalu masukkan field pertama.
    lines.insert(
        return_line_index + 1,
        indent + '    "developer_core": developer_runtime,'
    )

# ------------------------------------------------------------
# 9. Final syntax validation
# ------------------------------------------------------------
result = "\n".join(lines) + "\n"

compile(result, str(p), "exec")

p.write_text(result, encoding="utf-8")

print("=" * 60)
print("GATE 14 RUNTIME INTEGRATION REPAIR : PASS")
print("developer_runtime                  : CONNECTED")
print("developer_core response field      : CONNECTED")
print("SYNTAX                              : OK")
print("=" * 60)
