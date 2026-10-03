import json
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]

ENDPOINTS = [
    "/v1/health",
    "/v1/health/detail",
]


def check(url):
    try:
        with urlopen(url, timeout=15) as response:
            raw = response.read().decode("utf-8")

            try:
                data = json.loads(raw)
            except Exception:
                data = raw

            return True, response.status, data

    except Exception as exc:
        return False, None, str(exc)


def main():
    print("=" * 72)
    print("NUSANTARA AI PRODUCTION HEALTHCHECK")
    print("=" * 72)

    failed = 0

    for endpoint in ENDPOINTS:

        url = "http://127.0.0.1:8000" + endpoint

        ok, status, data = check(url)

        if ok:
            print()
            print(f"[PASS] {endpoint}")
            print(f"STATUS: {status}")

            if isinstance(data, dict):
                print(
                    json.dumps(
                        data,
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                print(data)

        else:
            failed += 1
            print()
            print(f"[FAIL] {endpoint}")
            print(data)

    print()
    print("=" * 72)

    if failed:
        print(
            f"HEALTHCHECK FAILED: {failed} endpoint(s)"
        )
        return 1

    print("HEALTHCHECK PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())