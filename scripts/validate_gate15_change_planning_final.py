"""
Gate 15 CHANGE PLANNING FINAL - Change Planning Engine Final Contract
(meta-validator).

GATE OBJECTIVE
  Verify that all Gate 15.5 / 15.6 / 15.7 sub-gate validators exist
  and PASS, and that the full status transition contract is declared
  consistently across the documentation contracts.

INPUT CONTRACT
  - scripts/validate_gate15_5_change_plan_schema.py exists
  - scripts/validate_gate15_6_change_plan_validator.py exists
  - scripts/validate_gate15_7_approval_wiring.py exists
  - Each of those three validators, when run, returns PASS
  - All three documentation files declare the status transition
    PROPOSED -> VALIDATED -> APPROVED -> IMPLEMENTED (or equivalent
    textual order).

PASS CRITERIA
  All five conditions above are met.

FAIL CRITERIA
  Any condition above is not met.

EVIDENCE OUTPUT
  Prints PASS/FAIL for each sub-validator and the overall final
  contract.

This is a meta-validator. The actual ChangePlan engine belongs to
the next engineering phase (post-approval per Section 7).

NOTE
  This validator itself does not call an LLM. Sub-validators are
  run as subprocesses.
"""
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]

SUB_VALIDATORS = [
    REPO / "scripts" / "validate_gate15_5_change_plan_schema.py",
    REPO / "scripts" / "validate_gate15_6_change_plan_validator.py",
    REPO / "scripts" / "validate_gate15_7_approval_wiring.py",
]

DOC_FILES = {
    "CLAUDE_CONTRACT.MD": REPO / "CLAUDE_CONTRACT.MD",
    "NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md": REPO / "docs" / "contracts" / "NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md",
    "GATES.md": REPO / "docs" / "audit" / "GATES.md",
}

STATUS_ORDER = [
    "PROPOSED",
    "VALIDATED",
    "APPROVED",
    "IMPLEMENTED",
]


def run_sub_validator(script: Path) -> tuple[bool, str]:
    if not script.exists():
        return False, "MISSING"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout or "") + (result.stderr or "")
        last_line = ""
        for line in output.splitlines():
            if "STATUS" in line and ":" in line:
                last_line = line.strip()
        passed = result.returncode == 0
        return passed, last_line or f"exit={result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as exc:
        return False, f"ERROR: {exc}"


def check_doc_status_contract(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    text = path.read_text(encoding="utf-8", errors="replace")
    # A status transition declaration must contain all four status
    # tokens in order on a single line (or a single transition
    # phrase). Adjective uses like "validated PASS" or "approved
    # knowledge" are excluded because we look for the explicit
    # transition pattern.
    pattern = (
        r"PROPOSED[^A-Z\n]*?VALIDATED[^A-Z\n]*?APPROVED[^A-Z\n]*?IMPLEMENTED"
    )
    compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    match = compiled.search(text)
    if match:
        return True, "transition line found"
    return False, "no PROPOSED->...->IMPLEMENTED transition declaration"


def main() -> int:
    print("NUSANTARA GATE 15 CHANGE PLANNING FINAL (META-VALIDATOR)")
    print("=" * 64)
    all_ok = True

    print("Sub-validators:")
    for script in SUB_VALIDATORS:
        ok, line = run_sub_validator(script)
        marker = "PASS" if ok else "FAIL"
        rel = script.relative_to(REPO)
        print(f"  [{marker}] {rel} -> {line}")
        if not ok:
            all_ok = False

    print("Documentation status contract:")
    for name, path in DOC_FILES.items():
        ok, msg = check_doc_status_contract(path)
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {msg}")
        if not ok:
            all_ok = False

    print("=" * 64)
    status = "PASS" if all_ok else "FAIL"
    print(f"GATE 15 CHANGE PLANNING FINAL STATUS : {status}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())