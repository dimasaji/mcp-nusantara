from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(r"C:\Users\dmaza\mcp-starter")
TARGET = ROOT / "developer_core_engine.py"

backup = TARGET.with_name(
    f"developer_core_engine.before_source_filter_{datetime.now():%Y%m%d_%H%M%S}.py"
)
shutil.copy2(TARGET, backup)

text = TARGET.read_text(encoding="utf-8")

start = text.find("def collect_source_files():")
end = text.find("\ndef ", start + 10)

if start == -1:
    raise SystemExit("collect_source_files() tidak ditemukan.")

if end == -1:
    end = len(text)

new_function = r'''def collect_source_files():
    """
    Mengambil source production yang relevan untuk Developer Core.

    Mengeluarkan:
    - backup
    - app_backup_*
    - *_backup
    - before_*
    - after_*
    - research
    - archive
    - quarantine
    - benchmark
    - cache
    - virtual environment
    """

    files = []

    excluded_exact_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "backup",
        "backups",
        "research",
        "archive",
        "archives",
        "quarantine",
        "benchmark",
        "node_modules",
        "graphify-out",
    }

    excluded_name_tokens = {
        ".bak",
        ".backup",
        "backup_",
        "_backup",
        "before_",
        "after_",
    }

    allowed_extensions = {
        ".py",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".md",
    }

    def is_blocked_part(part: str) -> bool:
        p = part.lower().strip()

        if not p:
            return False

        if p in excluded_exact_dirs:
            return True

        # Contoh:
        # app_backup_before_openrouter
        # backup_old
        # old_backup
        # before_openrouter
        # after_patch
        if p.startswith("app_backup_"):
            return True

        if p.startswith("backup_"):
            return True

        if p.endswith("_backup"):
            return True

        if p.startswith("before_"):
            return True

        if p.startswith("after_"):
            return True

        if p.startswith("backup-"):
            return True

        if p.endswith("-backup"):
            return True

        return False

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in allowed_extensions:
            continue

        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            continue

        # Periksa SEMUA komponen folder.
        blocked = False

        for part in relative.parts[:-1]:
            if is_blocked_part(part):
                blocked = True
                break

        if blocked:
            continue

        # Periksa nama file.
        name_lower = path.name.lower()

        if any(
            token in name_lower
            for token in excluded_name_tokens
        ):
            continue

        files.append(path)

    files.sort(
        key=lambda p: str(p).lower()
    )

    return files
'''

text = text[:start] + new_function + text[end:]

TARGET.write_text(text, encoding="utf-8")

print("PATCH SOURCE FILTER BERHASIL")
print("Backup:", backup)
