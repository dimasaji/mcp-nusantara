from pathlib import Path

p = Path(r".\app\knowledge\grounding.py")
s = p.read_text(encoding="utf-8")

old = '''    def _procedure_claim_supported(
        self,
        sentence: str,
        evidence_text: str,
    ) -> bool:
'''

if old not in s:
    raise SystemExit("METHOD _procedure_claim_supported TIDAK DITEMUKAN")

start = s.index(old)

# Cari method berikutnya setelah procedure method
next_def = s.find("\n    def ", start + len(old))

if next_def == -1:
    raise SystemExit("METHOD BERIKUTNYA TIDAK DITEMUKAN")

old_method = s[start:next_def]

new_method = '''    def _procedure_claim_supported(
        self,
        sentence: str,
        evidence_text: str,
    ) -> bool:
        """
        Procedure claims require explicit procedural evidence.

        A simple lexical overlap is not sufficient for claims such as:
        - harus melakukan ...
        - langkah ...
        - cara ...
        - pengguna harus ...
        - dapat dilakukan dengan ...

        Evidence that merely states a capability/status such as
        "status dapat diperiksa melalui layanan" must not automatically
        support a procedural instruction.
        """

        sentence_lower = self._normalize_text(sentence)
        evidence_lower = self._normalize_text(evidence_text)

        # Strong procedural markers.
        procedure_markers = [
            "langkah",
            "cara",
            "prosedur",
            "tahapan",
            "ikuti",
            "lakukan",
            "melakukan",
            "masukkan",
            "isi",
            "unggah",
            "upload",
            "pilih",
            "klik",
            "buka",
            "akses",
            "datang",
            "bawa",
            "ajukan",
            "mengajukan",
            "periksa",
            "cek",
            "mengecek",
        ]

        # Requirement/obligation markers are also procedural when they
        # describe what the user must do.
        obligation_markers = [
            "harus",
            "wajib",
            "perlu",
            "diharuskan",
        ]

        claim_has_procedure_marker = any(
            marker in sentence_lower
            for marker in procedure_markers
        )

        claim_has_obligation = any(
            marker in sentence_lower
            for marker in obligation_markers
        )

        # Evidence must explicitly contain procedural language too.
        evidence_has_procedure_marker = any(
            marker in evidence_lower
            for marker in procedure_markers
        )

        evidence_has_obligation = any(
            marker in evidence_lower
            for marker in obligation_markers
        )

        # If the sentence is procedural/obligatory but the evidence
        # contains no procedural or obligation marker, reject it.
        if claim_has_procedure_marker or claim_has_obligation:
            if not (
                evidence_has_procedure_marker
                or evidence_has_obligation
            ):
                return False

        # Preserve the existing lexical support rule as a secondary
        # condition, but never allow lexical overlap alone to establish
        # a procedural claim.
        sentence_tokens = set(
            self._tokenize(sentence_lower)
        )

        evidence_tokens = set(
            self._tokenize(evidence_lower)
        )

        if not sentence_tokens:
            return False

        overlap = len(sentence_tokens & evidence_tokens)
        ratio = overlap / max(len(sentence_tokens), 1)

        return ratio >= self.min_sentence_overlap

'''

s = s[:start] + new_method + s[next_def:]

p.write_text(s, encoding="utf-8")

print("=" * 70)
print("GROUNDING PROCEDURE HARDENING")
print("=" * 70)
print("PATCH : PASS")
print("FILE  :", p.resolve())
print("CHANGE: procedural claims require explicit procedural evidence")
