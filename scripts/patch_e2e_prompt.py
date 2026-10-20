from pathlib import Path
import re

p = Path(r".\scripts\test_e2e_grounding_ollama.py")
s = p.read_text(encoding="utf-8")

# Cari blok prompt yang dimulai dari system_instruction sampai JAWABAN.
pattern = re.compile(
    r'prompt\s*=\s*f"""[\s\S]*?JAWABAN:\s*"""',
    re.MULTILINE
)

new_prompt = '''prompt = f"""Jawab pertanyaan hanya berdasarkan EVIDENCE.

EVIDENCE:
{evidence_context}

PERTANYAAN:
{query}

ATURAN:
- Jangan menggunakan pengetahuan di luar EVIDENCE.
- Jangan membuat fakta baru.
- Jangan membuat prosedur, syarat, angka, atau contoh baru.
- Jika jawabannya ada di EVIDENCE, gunakan kalimat dari EVIDENCE.
- Jika jawabannya tidak ada, jawab: "Informasi tersebut belum tersedia dalam EVIDENCE."

JAWABAN:
"""'''

m = pattern.search(s)

if not m:
    print("=" * 70)
    print("PATCH : FAIL")
    print("ALASAN: blok prompt f-string tidak ditemukan")
    print("=" * 70)
    print()
    print("STRUKTUR PROMPT AKTUAL:")
    
    for i, line in enumerate(s.splitlines(), 1):
        if "prompt" in line.lower() or "EVIDENCE" in line or "JAWABAN" in line:
            print(f"{i}: {line}")
    
    raise SystemExit(1)

s = s[:m.start()] + new_prompt + s[m.end():]

p.write_text(s, encoding="utf-8")

print("=" * 70)
print("E2E PROMPT HARDENING")
print("=" * 70)
print("PATCH : PASS")
print("FILE  :", p.resolve())
print("MODE  : minimal evidence-only")
print()
print("Prompt lama berhasil diganti.")
