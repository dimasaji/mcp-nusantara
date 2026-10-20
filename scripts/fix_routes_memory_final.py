from pathlib import Path

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8")

bad = '''            _gate_integration.remember_response(
                session_id=request.session_id,
                response=response_text,
            )

            "response": response_text,
'''

good = '''            "response": response_text,
'''

if bad not in s:
    print("PATTERN TIDAK DITEMUKAN")
    raise SystemExit(1)

s = s.replace(bad, good, 1)

# Pastikan remember_response berada SETELAH response selesai dibuat.
marker = '''        return {
'''
idx = s.find(marker)
# Jangan gunakan marker pertama; cari blok return response utama
target = '''            "response": response_text,
            "evidence": evidence,
'''
pos = s.find(target)

if pos == -1:
    print("TARGET RESPONSE TIDAK DITEMUKAN")
    raise SystemExit(1)

# Cari penutup dictionary return setelah target
close = s.find('        }', pos)
if close == -1:
    print("PENUTUP RESPONSE TIDAK DITEMUKAN")
    raise SystemExit(1)

insert_at = close + len('        }')

memory_code = '''

        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )
'''

# Hindari duplikasi
if '_gate_integration.remember_response(' not in s:
    s = s[:insert_at] + memory_code + s[insert_at:]

p.write_text(s, encoding="utf-8")

compile(compile(s, str(p), "exec"), str(p), "exec")

print("ROUTES MEMORY PATCH : PASS")
print("SYNTAX : OK")
print("remember_response count:", s.count("_gate_integration.remember_response("))
