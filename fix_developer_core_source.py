from pathlib import Path
import shutil
from datetime import datetime
import py_compile
import re

TARGET = Path("developer_core_engine.py")

if not TARGET.exists():
    raise SystemExit("developer_core_engine.py tidak ditemukan.")

text = TARGET.read_text(encoding="utf-8")

# ============================================================
# BACKUP
# ============================================================

backup = TARGET.with_name(
    f"developer_core_engine.before_source_cleanup_{datetime.now():%Y%m%d_%H%M%S}.py"
)

shutil.copy2(TARGET, backup)

print("Backup:", backup.name)

# ============================================================
# 1. CARI collect_source_files
# ============================================================

start = text.find("def collect_source_files(")
end = text.find("\ndef build_source_index(", start)

if start == -1 or end == -1:
    raise SystemExit(
        "collect_source_files() tidak ditemukan."
    )

new_function = r'''
def collect_source_files():
    """
    Mengambil source production untuk Developer Core.

    File patch, backup, cache, hasil eksperimen dan
    generated output tidak dimasukkan ke Source RAG.
    """

    files = []

    excluded_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "backup",
        "backups",
        "research",
        "archive",
        "archives",
        "quarantine",
        "benchmark",
        "node_modules",
        "graphify-out",
        "dist",
        "build",
    }

    excluded_name_tokens = {
        ".bak",
        ".backup",
        "backup_",
        "_backup",
        "before_",
        "_before_",
        "after_",
        "_after_",
        "patch_",
        "_patch",
    }

    allowed_extensions = {
        ".py",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
    }

    # Source utama project
    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in allowed_extensions:
            continue

        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            continue

        parts_lower = {
            str(part).lower()
            for part in relative.parts
        }

        # Jangan masukkan directory non-production
        if parts_lower.intersection(excluded_dirs):
            continue

        name_lower = path.name.lower()

        # Jangan masukkan patch/backup
        if any(
            token in name_lower
            for token in excluded_name_tokens
        ):
            continue

        # Jangan masukkan file hasil temporary patch
        if name_lower.startswith("patch"):
            continue

        # Jangan masukkan file pyc
        if path.suffix.lower() == ".pyc":
            continue

        files.append(path)

    return sorted(
        set(files),
        key=lambda x: str(x).lower(),
    )
'''

text = (
    text[:start]
    + new_function
    + text[end:]
)

# ============================================================
# 2. PASTIKAN HELPER PRODUCTION RAG TETAP ADA
# ============================================================

required_helpers = [
    "def get_production_rag(",
    "def search_production_knowledge(",
    "def build_production_evidence_text(",
]

for helper in required_helpers:
    print(
        helper,
        "=>",
        helper in text,
    )

# ============================================================
# 3. TAMPILKAN LOKASI PRODUCTION EVIDENCE
# ============================================================

for marker in [
    "production_evidence = search_production_knowledge(",
    "production_evidence_text =",
]:

    positions = [
        m.start()
        for m in re.finditer(
            re.escape(marker),
            text,
        )
    ]

    print(
        marker,
        "COUNT =",
        len(positions),
        "LINES =",
        [
            text[:p].count("\n") + 1
            for p in positions
        ],
    )

# ============================================================
# SIMPAN
# ============================================================

TARGET.write_text(
    text,
    encoding="utf-8",
)

# ============================================================
# VALIDASI
# ============================================================

try:

    py_compile.compile(
        str(TARGET),
        doraise=True,
    )

    print()
    print("==========================================")
    print("DEVELOPER CORE SYNTAX : OK")
    print("SOURCE RAG CLEANUP    : OK")
    print("==========================================")
    print()
    print("Backup:", backup.name)

except Exception as exc:

    print()
    print("SYNTAX ERROR:")
    print(exc)
    print()
    print("RESTORE BACKUP...")

    shutil.copy2(
        backup,
        TARGET,
    )

    raise
