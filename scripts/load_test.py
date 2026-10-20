"""Bounded HTTP load measurement; default health only, chat is explicit."""
from __future__ import annotations
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit


def run(base_url: str, requests: int, concurrency: int, timeout: float, chat: bool = False) -> dict:
    origin = urlsplit(base_url)
    if origin.scheme not in {"http", "https"} or not origin.hostname or origin.username or origin.password:
        raise ValueError("invalid base URL")
    if not 1 <= requests <= 200 or not 1 <= concurrency <= 8 or not 0 < timeout <= 120:
        raise ValueError("load limits: requests<=200, concurrency<=8, timeout<=120")
    def call(index):
        start = time.perf_counter()
        try:
            data = json.dumps({"user_input": "Halo", "session_id": f"load-{index}", "stream": False}).encode() if chat else None
            req = Request(base_url.rstrip("/") + ("/v1/chat" if chat else "/v1/health"), data=data,
                          headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                payload = json.loads(response.read(2_000_000))
                ok = response.status == 200 and (bool(payload.get("response")) if chat else payload.get("status") == "ok")
            error = None
        except Exception as exc:
            ok, error = False, type(exc).__name__
        return {"ok": ok, "latency_ms": round((time.perf_counter() - start) * 1000, 2), "error_type": error}
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(call, range(requests)))
    latency = sorted(r["latency_ms"] for r in results)
    return {"captured_at": datetime.now(timezone.utc).isoformat(), "base_url": base_url,
            "scope": "chat" if chat else "health", "requests": requests, "concurrency": concurrency,
            "failures": sum(not r["ok"] for r in results), "elapsed_s": round(time.perf_counter() - started, 2),
            "p50_ms": latency[len(latency)//2], "p95_ms": latency[min(len(latency)-1,int(len(latency)*.95))],
            "records": results, "limitations": "Measurement only; no production SLA or answer quality inferred."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8002")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--chat", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.base_url, args.requests, args.concurrency, args.timeout, args.chat)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), "utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "records"},indent=2))
    sys.exit(bool(result["failures"]))
