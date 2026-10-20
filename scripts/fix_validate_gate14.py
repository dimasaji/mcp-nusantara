from pathlib import Path

p = Path("scripts/validate_gate14.py")
s = p.read_text(encoding="utf-8")

header = '''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

'''

# Buang import Path lama agar tidak duplikat.
s = s.replace("from pathlib import Path\nimport json\n", "")

# Buang header lama jika script sudah pernah dipatch.
marker = "from app.developer_core.engine import DeveloperCoreEngine"
idx = s.find(marker)

if idx == -1:
    print("Import DeveloperCore tidak ditemukan.")
    raise SystemExit(1)

s = header + s[idx:]

p.write_text(s, encoding="utf-8")

compile(s, str(p), "exec")

print("VALIDATOR IMPORT PATCH : PASS")
print("ROOT:", ROOT)
print("SYNTAX: OK")
