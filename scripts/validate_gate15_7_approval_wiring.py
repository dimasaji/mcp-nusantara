"""
Gate 15.7 - APPROVAL WIRING (meta-validator).

GATE OBJECTIVE
  Verify that documentation contracts consistently declare Gate 15.7
  sub-gate for approval wiring into the existing ApprovalQueue +
  AuditTrail pipeline.

INPUT CONTRACT
  - CLAUDE_CONTRACT.MD must declare Gate 15.7
  - docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md must
    declare Gate 15.7 verification requirement
  - docs/audit/GATES.md must declare Gate 15.7 acceptance
  - Live code references to ApprovalQueue and AuditTrail must
    remain present (no post-signature removal of existing approval
    infrastructure).

PASS CRITERIA
  All three documentation files contain the sub-gate marker AND
  the live code references are present.

FAIL CRITERIA
  Any documentation file missing the sub-gate marker, or any
  required live code reference removed.

EVIDENCE OUTPUT
  Prints PASS/FAIL with file-level and code-level evidence.

This is a documentation-contract + minimal live-code check. The
actual wiring implementation belongs to the next engineering phase.

NOTE
  This validator itself does not call an LLM.
"""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]

DOC_FILES = {
    "CLAUDE_CONTRACT.MD": REPO / "CLAUDE_CONTRACT.MD",
    "NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md": REPO / "docs" / "contracts" / "NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md",
    "GATES.md": REPO / "docs" / "audit" / "GATES.md",
}

MARKERS = [
    "Gate 15.7",
    "Approval Wiring",
]

# Live code references to ApprovalQueue and AuditTrail.
# These are part of the locked approval stack (per Section 31
# regression) and must remain present after the Gate 15.5+ work.
CODE_REFS = {
    "ApprovalQueue": REPO / "app" / "approval" / "queue.py",
    "AuditTrail": REPO / "app" / "approval" / "audit_trail.py",
}


def check_doc_file(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["MISSING"]
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    missing = [m for m in MARKERS if m.lower() not in lowered]
    return len(missing) == 0, missing


def check_code_ref(name: str, path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return name in text


def main() -> int:
    print("NUSANTARA GATE 15.7 - APPROVAL WIRING (META-VALIDATOR)")
    print("-" * 64)
    all_ok = True

    print("Documentation files:")
    for name, path in DOC_FILES.items():
        ok, missing = check_doc_file(path)
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}")
        if not ok:
            all_ok = False
            for m in missing:
                print(f"      missing marker: {m!r}")

    print("Live code references:")
    for name, path in CODE_REFS.items():
        ok = check_code_ref(name, path)
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name} ({path.relative_to(REPO)})")
        if not ok:
            all_ok = False

    print("-" * 64)
    status = "PASS" if all_ok else "FAIL"
    print(f"GATE 15.7 STATUS    : {status}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())