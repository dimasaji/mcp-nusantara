from pathlib import Path

p = Path(r".\app\knowledge\grounding.py")
s = p.read_text(encoding="utf-8")

# ============================================================
# 1. Tampilkan PROCEDURE_MARKERS aktual
# ============================================================

start = s.find("PROCEDURE_MARKERS")

print("=" * 70)
print("CURRENT PROCEDURE_MARKERS")
print("=" * 70)

if start >= 0:
    print(s[start:start + 1200])
else:
    print("PROCEDURE_MARKERS tidak ditemukan")

# ============================================================
# 2. Tambahkan marker wajib untuk klaim prosedural
# ============================================================

old = '''    def _contains_procedure_claim(
        self,
        sentence: str,
    ) -> bool:
        lower = sentence.lower()

        return any(
            marker in lower
            for marker in self.PROCEDURE_MARKERS
        )
'''

if old not in s:
    raise SystemExit(
        "ERROR: fungsi _contains_procedure_claim tidak ditemukan "
        "dalam format yang diharapkan."
    )

new = '''    def _contains_procedure_claim(
        self,
        sentence: str,
    ) -> bool:
        """
        Detect procedural/action claims.

        A sentence is procedural when it contains explicit
        action/instruction language OR an obligation combined
        with an action.
        """

        lower = self._normalize_text(sentence).lower()

        # Explicit procedural markers.
        explicit_markers = (
            "langkah",
            "cara",
            "prosedur",
            "tahapan",
            "ikuti",
            "lakukan",
            "melakukan",
            "klik",
            "buka",
            "pilih",
            "masukkan",
            "isi",
            "unggah",
            "upload",
            "ajukan",
            "mengajukan",
            "datang",
            "bawa",
            "periksa",
            "cek",
            "mengecek",
        )

        # Obligation + action is definitely procedural.
        obligation_markers = (
            "harus",
            "wajib",
            "perlu",
            "diharuskan",
        )

        has_explicit = any(
            marker in lower
            for marker in explicit_markers
        )

        has_obligation = any(
            marker in lower
            for marker in obligation_markers
        )

        # Critical rule:
        # "harus melakukan ...", "wajib mengajukan ...",
        # etc. are procedural claims.
        if has_obligation and has_explicit:
            return True

        return has_explicit
'''

s = s.replace(old, new)

p.write_text(s, encoding="utf-8")

print("")
print("=" * 70)
print("PATCH")
print("=" * 70)
print("STATUS : PASS")
print("RULE   : 'harus' + action => procedural claim")
print("RULE   : 'melakukan' is procedural")
print("")
print("=" * 70)
print("DIRECT GUARD CHECK")
print("=" * 70)

from app.knowledge.grounding import EvidenceGroundingGuard

guard = EvidenceGroundingGuard()

answer = (
    "Untuk mengecek status KTP, pengguna harus melakukan "
    "pemeriksaan status melalui sistem layanan."
)

evidence = (
    "KTP-el adalah dokumen identitas penduduk. "
    "Status pengajuan KTP-el dapat diperiksa melalui "
    "layanan administrasi kependudukan."
)

print("contains_procedure_claim:",
      guard._contains_procedure_claim(answer))

print("evidence_contains_procedure_claim:",
      guard._evidence_contains_procedure_claim(evidence))

result = guard.validate(answer, evidence)

print("grounded:", result.grounded)
print("reason:", result.reason)
print("unsupported:", result.unsupported_sentences)

if result.grounded:
    raise SystemExit(
        "FAIL: E2E-002 masih dianggap grounded. "
        "Jangan lanjut ke test sebelum diagnostic ini False."
    )

print("")
print("DIRECT GUARD CHECK: PASS")
