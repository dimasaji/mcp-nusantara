from pathlib import Path

p = Path(r"C:\Users\dmaza\mcp-starter\developer_core_engine.py")
text = p.read_text(encoding="utf-8")

old = '    graph_nodes = GRAPH.get("nodes", [])'

new = '''    graph = load_graph()
    graph_nodes = graph.get("nodes", [])'''

if old not in text:
    raise SystemExit("Target GRAPH.get(...) tidak ditemukan. Tidak ada perubahan dilakukan.")

text = text.replace(old, new, 1)

p.write_text(text, encoding="utf-8")

print("FIX BERHASIL.")
print("search_graph() sekarang menggunakan load_graph().")
