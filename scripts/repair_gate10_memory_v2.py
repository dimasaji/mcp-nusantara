from pathlib import Path
import shutil

p = Path("app/api/routes.py")
backup = Path("app/api/routes.py.bak_gate10_final")

shutil.copy2(p, backup)

lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

# ------------------------------------------------------------
# 1. Cari semua remember_response()
# ------------------------------------------------------------
starts = []
for i, line in enumerate(lines):
    if "_gate_integration.remember_response(" in line:
        starts.append(i)

print("remember_response ditemukan:", len(starts))

# ------------------------------------------------------------
# 2. Hapus setiap blok remember_response sampai ")" penutup.
#    Kita hapus komentar Gate 10 yang menempel jika ada.
# ------------------------------------------------------------
remove = set()

for start in starts:
    # hapus komentar tepat sebelumnya jika merupakan komentar Gate 10
    j = start - 1
    while j >= 0 and not lines[j].strip():
        j -= 1

    if j >= 0 and "Gate 10 Memory" in lines[j]:
        remove.add(j)

    # hapus dari pemanggilan sampai closing )
    depth = 0
    found_open = False

    for k in range(start, len(lines)):
        text = lines[k]

        if "(" in text:
            depth += text.count("(")
            found_open = True

        if ")" in text:
            depth -= text.count(")")

        remove.add(k)

        if found_open and depth <= 0:
            break

print("Baris yang akan dipindahkan:", len(remove))

# Simpan isi tanpa remember_response
clean = [
    line for i, line in enumerate(lines)
    if i not in remove
]

# ------------------------------------------------------------
# 3. Cari FINAL return berdasarkan isi dictionary
# ------------------------------------------------------------
return_idx = None

for i, line in enumerate(clean):
    if line.strip() == "return {":
        # lihat 15 baris berikutnya
        window = "".join(clean[i:i+20])
        if '"session_id": request.session_id' in window:
            return_idx = i
            break

if return_idx is None:
    print("FINAL RETURN TIDAK DITEMUKAN.")
    print("")
    print("Return yang ditemukan:")
    for i, line in enumerate(clean):
        if line.strip() == "return {":
            print(i + 1, repr(line.rstrip()))

    # jangan merusak file
    shutil.copy2(backup, p)
    raise SystemExit(1)

# ------------------------------------------------------------
# 4. Masukkan memory tepat sebelum final return
# ------------------------------------------------------------
memory = [
    "        _gate_integration.remember_response(\n",
    "            session_id=request.session_id,\n",
    "            response=response_text,\n",
    "        )\n",
    "\n",
]

clean[return_idx:return_idx] = memory

# ------------------------------------------------------------
# 5. Pastikan hanya satu
# ------------------------------------------------------------
result = "".join(clean)

if result.count("_gate_integration.remember_response(") != 1:
    print("JUMLAH remember_response SALAH:",
          result.count("_gate_integration.remember_response("))
    shutil.copy2(backup, p)
    raise SystemExit(1)

# ------------------------------------------------------------
# 6. Syntax check sebelum menyimpan
# ------------------------------------------------------------
compile(result, str(p), "exec")

p.write_text(result, encoding="utf-8")

print("")
print("==============================================")
print("GATE 10 MEMORY REPAIR : PASS")
print("FINAL RETURN LINE     :", return_idx + 1)
print("remember_response     : 1")
print("SYNTAX                : OK")
print("BACKUP                :", backup)
print("==============================================")
