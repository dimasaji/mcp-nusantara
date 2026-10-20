from pathlib import Path

p = Path(r".\app\knowledge\grounding.py")
s = p.read_text(encoding="utf-8")

old = '''    def _evidence_contains_procedure_claim(
        self,
        evidence: str,
    ) -> bool:
        lower = evidence.lower()

        return any(
            marker in lower
            for marker in self.PROCEDURE_MARKERS
        )
'''

if old not in s:
    raise SystemExit(
        "ERROR: blok _evidence_contains_procedure_claim tidak ditemukan persis."
    )

new = '''    def _evidence_contains_procedure_claim(
        self,
        evidence: str,
    ) -> bool:
        """
        Detect EXPLICIT procedural instructions in evidence.

        Capability/status statements such as:
            "status dapat diperiksa melalui layanan"

        are NOT considered procedural evidence.

        Procedural evidence requires explicit action/instruction
        language such as:
            langkah, cara, lakukan, klik, buka, pilih, masukkan,
            unggah, isi, ajukan, datang, bawa, ikuti, tahapan,
            prosedur.
        """

        lower = self._normalize_text(evidence).lower()

        explicit_procedure_markers = (
            "langkah",
            "cara",
            "prosedur",
            "tahapan",
            "ikuti",
            "lakukan",
            "melakukan langkah",
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
        )

        return any(
            marker in lower
            for marker in explicit_procedure_markers
        )
'''

s = s.replace(old, new)

p.write_text(s, encoding="utf-8")

print("=" * 70)
print("NUSANTARA GROUNDING - PROCEDURE EVIDENCE HARDENING")
print("=" * 70)
print("STATUS : PATCHED")
print("")
print("Procedure evidence now requires explicit instruction markers.")
print("Capability/status words such as 'diperiksa' are NOT sufficient.")
print("")
print("RUNNING E2E TEST...")
