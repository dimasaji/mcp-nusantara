from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

print("=" * 72)
print("NUSANTARA AI - PRODUCTION INDOBERT BRIDGE HARDENING")
print("=" * 72)

commands = [
    [
        sys.executable,
        "-m",
        "app.knowledge.production_embedding_bridge",
        "self-test",
    ],
    [
        sys.executable,
        "-m",
        "app.knowledge.production_embedding_bridge",
        "stats",
    ],
]

for command in commands:

    print()
    print(
        "> " + " ".join(command)
    )

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    if result.returncode != 0:

        print()
        print(
            "INDOBERT BRIDGE HARDENING: FAILED"
        )

        raise SystemExit(
            result.returncode
        )

print()
print("=" * 72)
print("INDOBERT BRIDGE HARDENING: PASS")
print("=" * 72)
