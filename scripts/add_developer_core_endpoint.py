from pathlib import Path

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8")

marker = "@router.get(\"/developer-core\")"

if marker in s:
    print("ENDPOINT DEVELOPER CORE SUDAH ADA")
    raise SystemExit(0)

block = '''
@router.get("/developer-core")
async def developer_core_status():
    """Read-only Developer Core / Graphify runtime inspection."""
    return _developer_core.inspect()
'''

# Tambahkan di akhir file.
s = s.rstrip() + "\n\n" + block + "\n"

compile(s, str(p), "exec")
p.write_text(s, encoding="utf-8")

print("DEVELOPER CORE ENDPOINT : PASS")
print("ENDPOINT                : GET /v1/developer-core")
print("SYNTAX                  : OK")
