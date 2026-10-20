from pathlib import Path

p = Path(r".\app\knowledge\grounding.py")
s = p.read_text(encoding="utf-8")

start_marker = '''    def _procedure_claim_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
'''

start = s.find(start_marker)

if start == -1:
    raise SystemExit("ERROR: _procedure_claim_supported tidak ditemukan")

end = s.find("\n    # ============================================================", start + len(start_marker))

if end == -1:
    raise SystemExit("ERROR: akhir blok PROCEDURE VALIDATION tidak ditemukan")

new_method = '''    def _procedure_claim_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        """
        Procedure claims require explicit procedural evidence.

        Lexical overlap of one token is NOT sufficient.
        Evidence must contain procedural language and provide
        meaningful lexical support for the claimed action.
        """

        if not self._contains_procedure_claim(sentence):
            return True

        # Evidence must explicitly describe a procedure/action.
        if not self._evidence_contains_procedure_claim(evidence):
            return False

        sentence_tokens = self._meaningful_tokens(sentence)
        evidence_tokens = self._meaningful_tokens(evidence)

        if not sentence_tokens or not evidence_tokens:
            return False

        overlap = sentence_tokens & evidence_tokens

        # One shared token is too weak for a procedural claim.
        # Require at least 2 meaningful overlapping tokens.
        if len(overlap) < 2:
            return False

        # Require meaningful lexical coverage of the claim.
        coverage = len(overlap) / max(len(sentence_tokens), 1)

        # Procedure claims need stronger evidence than ordinary
        # informational statements.
        return coverage >= 0.30

'''

s = s[:start] + new_method + s[end:]

p.write_text(s, encoding="utf-8")

print("=" * 70)
print("NUSANTARA GROUNDING PROCEDURE PATCH")
print("=" * 70)
print("STATUS : PATCHED")
print("FILE   :", p.resolve())
print("RULE   : procedure claim requires explicit evidence")
print("RULE   : minimum 2 meaningful overlapping tokens")
print("RULE   : minimum 30% lexical coverage")
