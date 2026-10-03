from pathlib import Path
import shutil
import re

p = Path("app/api/routes.py")
backup = Path("app/api/routes.py.bak_gate10_fix")

# Backup
shutil.copy2(p, backup)
print("BACKUP:", backup)

s = p.read_text(encoding="utf-8")

# Hapus SEMUA pemanggilan remember_response yang berada sebelum
# return dictionary final.
pattern = re.compile(
    r'\n[ \t]*(?:#.*\n)?[ \t]*_gate_integration\.remember_response\(\s*'
    r'session_id=request\.session_id,\s*'
    r'response=response_text,\s*'
    r'\)\s*',
    re.MULTILINE,
)

matches = list(pattern.finditer(s))
print("remember_response ditemukan:", len(matches))

# Hapus semua occurrence terlebih dahulu.
s = pattern.sub("\n", s)

# Cari FINAL RESPONSE dictionary.
marker = '''        # 10. FINAL RESPONSE
        # ==============================================================

        return {
            "session_id": request.session_id,
'''

if marker not in s:
    print("Marker FINAL RESPONSE tidak ditemukan.")
    print("Mencari alternatif...")

    marker = '''        return {
            "session_id": request.session_id,
'''

if marker not in s:
    print("PATCH GAGAL: return final tidak ditemukan.")
    shutil.copy2(backup, p)
    raise SystemExit(1)

# Masukkan memory SEBELUM return dictionary.
replacement = '''        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

        return {
            "session_id": request.session_id,
'''

s = s.replace(marker, replacement, 1)

# Pastikan hanya satu remember_response.
count = s.count("_gate_integration.remember_response(")
if count != 1:
    print("PATCH GAGAL: remember_response count =", count)
    shutil.copy2(backup, p)
    raise SystemExit(1)

# Syntax validation sebelum menyimpan final.
compile(s, str(p), "exec")

p.write_text(s, encoding="utf-8")

print("")
print("==============================================")
print("GATE 10 MEMORY REPAIR : PASS")
print("remember_response:", count)
print("SYNTAX            : OK")
print("BACKUP            :", backup)
print("==============================================")
