from pathlib import Path

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8-sig")

# Hapus semua blok remember_response yang salah.
start = "        # Store final assistant response in Gate 10 memory."
while start in s:
    pos = s.find(start)
    end = s.find("        return {", pos)
    if end == -1:
        # fallback: hapus sampai blok berikutnya yang tidak terlalu jauh
        end = s.find("\n\n", pos)
        if end == -1:
            end = len(s)
    s = s[:pos] + s[end:]

# Masukkan memory tepat sebelum response final dikembalikan.
marker = '            "response": response_text,'

if "_gate_integration.remember_response(" not in s:
    if marker not in s:
        raise SystemExit("RESPONSE MARKER NOT FOUND")

    block = """        # Gate 10 Memory — store final assistant response.
        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

"""

    s = s.replace(marker, block + marker, 1)

p.write_text(s, encoding="utf-8")

print("GATE 10 MEMORY POSITION : PASS")
