import json
import subprocess
import sys
import time


PYTHON = sys.executable
WORKER = r".\nusantara-models\indobert_worker.py"


process = subprocess.Popen(
    [PYTHON, WORKER],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


# ============================================================
# TUNGGU WORKER READY
# ============================================================

print("Menunggu IndoBERT worker...")

while True:
    line = process.stderr.readline()

    if not line:
        break

    print("WORKER:", line.strip())

    if '"event": "ready"' in line:
        break


# ============================================================
# KIRIM REQUEST
# ============================================================

texts = [
    "Saya mau cek status KTP saya",
    "KTP saya sudah selesai belum?",
    "Bagaimana cara melihat status KTP?",
]


for text in texts:

    request = {
        "text": text
    }

    request_json = json.dumps(
        request,
        ensure_ascii=False
    )

    print()
    print("REQUEST:", request_json)

    start = time.perf_counter()

    try:
        process.stdin.write(request_json + "\n")
        process.stdin.flush()

        response = process.stdout.readline()

        elapsed = time.perf_counter() - start

        if not response:
            print("ERROR: Worker tidak memberikan response.")
            break

        result = json.loads(response)

        print("OK:", result.get("ok"))
        print("ENGINE:", result.get("engine"))
        print("MODEL:", result.get("model"))
        print("DIMENSION:", result.get("dimension"))
        print(
            "INFERENCE:",
            result.get("inference_seconds"),
            "seconds"
        )
        print(
            "ROUND TRIP:",
            round(elapsed, 4),
            "seconds"
        )

    except BrokenPipeError:
        print("ERROR: stdin worker tertutup.")
        break

    except Exception as exc:
        print("ERROR:", repr(exc))
        break


# ============================================================
# STOP WORKER
# ============================================================

try:
    process.stdin.close()
except Exception:
    pass

process.terminate()

try:
    process.wait(timeout=5)
except subprocess.TimeoutExpired:
    process.kill()
    process.wait()