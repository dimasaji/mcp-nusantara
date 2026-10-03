from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

commands = [
    [
        sys.executable,
        "-m",
        "app.knowledge.production_kb",
        "self-test",
    ],
    [
        sys.executable,
        "-m",
        "app.knowledge.production_kb",
        "stats",
    ],
]

print("=" * 72)
print("NUSANTARA AI - PRODUCTION KNOWLEDGE BASE HARDENING")
print("=" * 72)

for command in commands:

    print()
    print(">", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    if result.returncode != 0:
        print()
        print("PRODUCTION KB HARDENING: FAILED")
        raise SystemExit(result.returncode)

print()
print("=" * 72)
print("PRODUCTION KB HARDENING: PASS")
print("=" * 72)
