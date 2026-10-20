from pathlib import Path
import shutil
import py_compile

current = Path("developer_core_engine.py")
backup = Path("developer_core_engine.before_graph_rag_production_20261002_142501.py")

if not backup.exists():
    print("ERROR: backup tidak ditemukan:")
    print(backup)
    raise SystemExit(1)

# Pulihkan file sebelum patch yang bermasalah
shutil.copy2(backup, current)

print("RESTORE:")
print(" ", backup)
print(" ->")
print(" ", current)

# Validasi syntax
py_compile.compile(
    str(current),
    doraise=True,
)

print()
print("=" * 60)
print("RESTORE BERHASIL")
print("SYNTAX : OK")
print("=" * 60)

# Cek bahwa FastAPI app kembali tersedia
text = current.read_text(encoding="utf-8")

checks = {
    "app = FastAPI": "app = FastAPI" in text,
    "graph_rag": "def graph_rag(" in text,
    "ProductionHybridRAG": "ProductionHybridRAG" in text,
    "search_production_knowledge": "def search_production_knowledge(" in text,
}

print()
for name, value in checks.items():
    print(f"{name:35} = {value}")
