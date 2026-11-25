"""
Gate 15.6 - CHANGE PLAN VALIDATOR (meta-validator).

GATE OBJECTIVE
  Verify that documentation contracts consistently declare Gate 15.6
  sub-gate for the deterministic Change Plan Validator (no LLM per
  CLAUDE_CONTRACT.MD Section 44).

INPUT CONTRACT
  - CLAUDE_CONTRACT.MD must declare Gate 15.6 and the no-LLM rule
  - docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md must
    declare Gate 15.6 verification requirement
  - docs/audit/GATES.md must declare Gate 15.6 acceptance

PASS CRITERIA
  All three files contain the sub-gate marker and the no-LLM rule.

FAIL CRITERIA
  Any file missing the sub-gate marker or no-LLM rule.

EVIDENCE OUTPUT
  Prints PASS/FAIL with file-level evidence.

This is a documentation-contract meta-validator. The actual
deterministic validator implementation belongs to the next
engineering phase (post-approval per Section 7).

NOTE
  This validator itself does not call an LLM.
"""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]

FILES = {
    "CLAUDE_CONTRACT.MD": REPO / "CLAUDE_CONTRACT.MD",
    "NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md": REPO / "docs" / "contracts" / "NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md",
    "GATES.md": REPO / "docs" / "audit" / "GATES.md",
}

MARKERS = [
    "Gate 15.6",
    "Change Plan Validator",
]

NO_LLM_RULES = [
    # Each file must include at least one of these phrases
    # declaring the no-LLM rule for the validator.
    "no LLM",
    "deterministic",
]


def _has_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(p.lower() in lowered for p in phrases)


def check_file(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["MISSING"]
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    missing_markers = [m for m in MARKERS if m.lower() not in lowered]
    has_rule = _has_any(text, NO_LLM_RULES)
    failures = list(missing_markers)
    if not has_rule:
        failures.append("no-LLM rule")
    return len(failures) == 0, failures


def main() -> int:
    print("NUSANTARA GATE 15.6 - CHANGE PLAN VALIDATOR (META-VALIDATOR)")
    print("-" * 64)
    all_ok = True
    for name, path in FILES.items():
        ok, failures = check_file(path)
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] {name}")
        if not ok:
            all_ok = False
            for f in failures:
                print(f"    missing: {f!r}")
    print("-" * 64)
    status = "PASS" if all_ok else "FAIL"
    print(f"GATE 15.6 STATUS    : {status}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())