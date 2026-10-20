from pathlib import Path
import ast
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "v2" / "hermes_adapter.py"
BACKUP_DIR = ROOT / "docs" / "audit" / "backups"

source = TARGET.read_text(encoding="utf-8-sig")
ast.parse(source, filename=str(TARGET))

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_DIR / f"hermes_adapter.py.{stamp}.bak"
shutil.copy2(TARGET, backup)

old = '''    def run(
        self,
        *,
        user_input: str,
        session_id: str,
        evidence: list[Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
'''

new = '''    def run(
        self,
        user_input: str,
        session_id: str,
        evidence: list[Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
'''

if old not in source:
    raise RuntimeError("Signature adapter tidak ditemukan. Tidak ada perubahan.")

source = source.replace(old, new, 1)

ast.parse(source, filename=str(TARGET))
compile(source, str(TARGET), "exec")

TARGET.write_text(source, encoding="utf-8", newline="")

print("=" * 72)
print("HERMES V2 ADAPTER CALLABLE PATCH")
print("=" * 72)
print("AST     : PASS")
print("COMPILE : PASS")
print(f"TARGET  : {TARGET}")
print(f"BACKUP  : {backup}")
print("PATCH   : COMPLETE")
