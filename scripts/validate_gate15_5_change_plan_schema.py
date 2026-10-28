"""
Gate 15.5 - CHANGE PLAN SCHEMA (meta-validator).

GATE OBJECTIVE
  Verify that documentation contracts consistently declare Gate 15.5
  sub-gate for Change Plan Schema with the 14-field schema contract.

INPUT CONTRACT
  - CLAUDE_CONTRACT.MD must contain Gate 15.5 declaration
  - docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md must
    contain Gate 15.5 verification requirement
  - docs/audit/GATES.md must contain Gate 15.5 acceptance

PASS CRITERIA
  All three files contain the sub-gate marker.

FAIL CRITERIA
  Any of the three files missing the sub-gate marker, or
  inconsistent sub-gate label.

EVIDENCE OUTPUT
  Prints PASS/FAIL with file-level evidence.

This is a documentation-contract meta-validator. The actual
ChangePlan dataclass implementation belongs to the next engineering
phase (post-approval per Section 7).

NOTE
  No LLM is used in this validator per CLAUDE_CONTRACT.MD Section 44.
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
    "Gate 15.5",
    "Change Plan Schema",
]


def check_file(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["MISSING"]
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    missing = [m for m in MARKERS if m.lower() not in lowered]
    return len(missing) == 0, missing


def main() -> int:
    print("NUSANTARA GATE 15.5 - CHANGE PLAN SCHEMA (META-VALIDATOR)")
    print("-" * 64)
    all_ok = True
    for name, path in FILES.items():
        ok, missing = check_file(path)
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] {name}")
        if not ok:
            all_ok = False
            for m in missing:
                print(f"    missing marker: {m!r}")
    print("-" * 64)
    status = "PASS" if all_ok else "FAIL"
    print(f"GATE 15.5 STATUS    : {status}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())