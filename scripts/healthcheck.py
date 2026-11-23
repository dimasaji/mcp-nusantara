import json
import os
import urllib.error
import urllib.request


def main() -> int:
    port = os.getenv("NUSANTARA_HEALTHCHECK_PORT", "18201")
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            if response.status != 200:
                return 1
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return 1
    return 0 if isinstance(payload, dict) and payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
