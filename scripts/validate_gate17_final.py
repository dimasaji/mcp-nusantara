from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACTS = [
    ("17.1", "validate_gate17_gap.py", "GATE 17.1 FINAL"),
    ("17.2", "validate_gate17_evidence.py", "GATE 17.2 FINAL"),
    ("17.3", "validate_gate17_root_cause.py", "GATE 17.3 FINAL"),
    ("17.4", "validate_gate17_proposal.py", "GATE 17.4 FINAL"),
    ("17.5", "validate_gate17_experiment.py", "GATE 17.5 FINAL"),
    ("17.6", "validate_gate17_evaluation.py", "GATE 17.6 FINAL"),
]

results = []

print("=" * 72)
print("NUSANTARA GATE 17 FINAL")
print("CONTINUOUS IMPROVEMENT CONTRACT")
print("=" * 72)

for gate, script, marker in CONTRACTS:
    path = ROOT / "scripts" / script

    print(f"\n[{gate}] {script}")

    if not path.exists():
        print("  [FAIL] validator tidak ditemukan")
        results.append({
            "gate": gate,
            "script": script,
            "status": "FAIL",
            "reason": "validator_missing",
        })
        continue

    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = proc.stdout + proc.stderr
    passed = (
        proc.returncode == 0
        and marker in output
        and "PASS" in output
        and "FAIL              : 0" in output
    )

    status = "PASS" if passed else "FAIL"

    print(f"  STATUS : {status}")

    results.append({
        "gate": gate,
        "script": script,
        "marker": marker,
        "status": status,
        "returncode": proc.returncode,
    })

all_pass = all(item["status"] == "PASS" for item in results)

contract = {
    "contract": "NUSANTARA GATE 17 FINAL",
    "version": "1.0",
    "status": "PASS" if all_pass else "FAIL",
    "production_write": False,
    "execution": False,
    "approval_required": True,
    "deterministic": True,
    "contracts": results,
}

output_dir = ROOT / "graphify-out"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "gate17_final_contract.json"

output_file.write_text(
    json.dumps(
        contract,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

print("\n" + "-" * 72)
print(f"CONTRACTS          : {len(results)}")
print(f"PASS               : {sum(x['status'] == 'PASS' for x in results)}")
print(f"FAIL               : {sum(x['status'] == 'FAIL' for x in results)}")
print("-" * 72)

if all_pass:
    print("GATE 17 FINAL      : PASS")
    print("PRODUCTION WRITE   : NOT ENABLED")
    print("EXECUTION          : NOT ENABLED")
    print("APPROVAL           : REQUIRED")
    print("EVALUATION         : DETERMINISTIC")
else:
    print("GATE 17 FINAL      : FAIL")
    raise SystemExit(1)

print("-" * 72)
print(f"OUTPUT             : {output_file}")
print("=" * 72)
