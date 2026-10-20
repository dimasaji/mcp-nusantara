from pathlib import Path

p = Path(r".\app\knowledge\grounding.py")
s = p.read_text(encoding="utf-8")

marker = '''    # ============================================================
    # REQUIREMENT VALIDATION
    # ============================================================
'''

method = '''    # ============================================================
    # ABSTENTION VALIDATION
    # ============================================================

    def _is_valid_abstention(
        self,
        sentence: str,
    ) -> bool:
        """
        Accept a pure evidence-based abstention without requiring
        lexical overlap with the evidence.

        This is intentionally narrow:
        - accepts statements that explicitly say information is
          unavailable / not present in evidence
        - rejects abstentions that themselves contain requirement,
          procedure, or numeric claims

        Example accepted:
            "Informasi tersebut belum tersedia dalam EVIDENCE."

        Example rejected:
            "Syarat membuat KTP-el adalah ..."
        """
        lower = self._normalize_text(sentence).lower()

        if not lower:
            return False

        abstention_markers = (
            "tidak tersedia",
            "belum tersedia",
            "tidak ada informasi",
            "belum ada informasi",
            "tidak ditemukan informasi",
            "belum ditemukan informasi",
            "informasi tidak tersedia",
            "informasi tersebut tidak tersedia",
            "informasi tersebut belum tersedia",
            "evidence tidak memenuhi",
            "evidence tidak memiliki",
            "tidak terdapat informasi",
            "tidak terdapat data",
            "belum terdapat informasi",
        )

        if not any(
            marker in lower
            for marker in abstention_markers
        ):
            return False

        # A refusal containing a concrete high-risk claim is NOT
        # a pure abstention and must still be grounded normally.
        if self._contains_requirement_claim(sentence):
            return False

        if self._contains_procedure_claim(sentence):
            return False

        if self._contains_numeric_claim(sentence):
            return False

        return True

'''

if "def _is_valid_abstention(" not in s:
    if marker not in s:
        raise SystemExit("MARKER REQUIREMENT VALIDATION TIDAK DITEMUKAN")

    s = s.replace(
        marker,
        method + marker,
        1,
    )

validate_marker = '''        evidence_texts = [
            item["text"]
            for item in evidence_items
            if item["text"]
        ]

        combined_evidence = " ".join(evidence_texts)

        question_type = self._normalize_intent(
            intent_name
        )

        sentences = self._split_sentences(text)
'''

validate_replacement = '''        evidence_texts = [
            item["text"]
            for item in evidence_items
            if item["text"]
        ]

        combined_evidence = " ".join(evidence_texts)

        question_type = self._normalize_intent(
            intent_name
        )

        sentences = self._split_sentences(text)

        # --------------------------------------------------------
        # VALID EVIDENCE-BASED ABSTENTION
        # --------------------------------------------------------
        # A pure abstention is allowed only when it does not contain
        # a requirement, procedure, or numeric claim. This prevents
        # the guard from treating a legitimate "information is not
        # available" response as hallucinated content while keeping
        # high-risk claims fail-closed.
        if (
            len(sentences) == 1
            and self._is_valid_abstention(sentences[0])
        ):
            return GroundingResult(
                text=text,
                grounded=True,
                reason="grounded_abstention",
                unsupported_sentences=[],
            )
'''

if validate_marker not in s:
    raise SystemExit("BLOK VALIDATE TARGET TIDAK DITEMUKAN")

s = s.replace(
    validate_marker,
    validate_replacement,
    1,
)

p.write_text(s, encoding="utf-8")

print("=" * 70)
print("GROUNDING ABSTENTION PATCH")
print("=" * 70)
print("PATCH : PASS")
print("FILE  :", p.resolve())
print()
print("Added : _is_valid_abstention()")
print("Added : grounded_abstention result")
print()
