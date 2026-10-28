#!/usr/bin/env python3
"""Phase 12: evaluate the live V1 API; --mock explicitly runs harness smoke tests."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.evaluation import EvalCase, compare, load_baseline, run_cases, save_baseline  # noqa: E402


def mock_system(query: str) -> dict:
    if "ktp" in query:
        return {"answer": "Biaya KTP gratis", "evidence": ["Biaya KTP gratis"], "retrieved_doc_ids": ["ktp"]}
    if "hitung" in query:
        return {"answer": "36", "tool_called": "calculator"}
    if "gaji" in query:
        return {"answer": "Perlu peninjauan manusia", "policy_decision": "REQUIRE_HUMAN"}
    return {"answer": "Halo, baik.", "tool_called": None}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class V1System:
    """Evaluate chat with a fresh session for every attempt; no ingest or admin calls."""

    def __init__(self, base_url: str, timeout: float = 60):
        url = urlsplit(base_url)
        if (url.scheme not in {"http", "https"} or not url.hostname or url.username
                or url.password or url.query or url.fragment or url.path not in {"", "/"}):
            raise ValueError("base-url must be an HTTP(S) origin without credentials")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.opener = build_opener(NoRedirect())

    def request(self, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(self.base_url + path, data=body,
                      headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=self.timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("API response exceeded evaluation size limit")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("API response must be an object")
        return data

    def __call__(self, query: str) -> dict:
        data = self.request("/v1/chat", {"user_input": query,
                            "session_id": "eval-" + uuid.uuid4().hex, "stream": False})
        answer = data.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("V1 response must contain a nonempty response string")
        evidence = data.get("evidence", [])
        if not isinstance(evidence, list):
            raise ValueError("V1 evidence must be a list")
        texts, ids = [], []
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError("V1 evidence entries must be objects")
            # A title or source URL alone does not support factual claims.
            if isinstance(item.get("chunk"), str) and item["chunk"].strip():
                texts.append(item["chunk"])
            if isinstance(item.get("document_id"), str):
                ids.append(item["document_id"])
        return {"answer": answer, "evidence": texts, "retrieved_doc_ids": ids,
                "metadata": {k: data[k] for k in (
                    "session_id", "request_id", "model", "provider_status", "grounding", "timestamp"
                ) if k in data}}


def positive_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--timeout", type=positive_float, default=60)
    parser.add_argument("--latency-target-ms", type=positive_float, default=2000)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("repeats must be at least 1")
    dataset = args.dataset or ROOT / "app/evaluation/datasets" / (
        "smoke_id.json" if args.mock else "v1_id.json")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or ROOT / "audit_reports" / f"EVAL_{'MOCK' if args.mock else 'V1'}_{stamp}.json"
    try:
        dataset_bytes = dataset.read_bytes()
        rows = json.loads(dataset_bytes)
        if not isinstance(rows, list) or not rows:
            raise ValueError("dataset must be a nonempty list")
        cases = [EvalCase(**row) for row in rows]
        if (len({c.case_id for c in cases}) != len(cases)
                or any(not c.case_id or not c.query.strip() for c in cases)):
            raise ValueError("dataset needs unique IDs and nonempty queries")
        baseline = load_baseline(args.baseline) if args.baseline else None
        if baseline is not None:
            if output.resolve() == args.baseline.resolve():
                raise ValueError("output must not overwrite the reference baseline")
            meta = baseline.get("meta", {})
            if (meta.get("mode") != ("mock" if args.mock else "live_v1")
                    or meta.get("dataset_sha256") != hashlib.sha256(dataset_bytes).hexdigest()
                    or meta.get("repeats") != args.repeats
                    or meta.get("latency_target_ms") != args.latency_target_ms):
                raise ValueError("baseline mode, dataset and evaluation settings must match")
        health = None
        if args.mock:
            system = mock_system
        else:
            system = V1System(args.base_url, args.timeout)
            health = system.request("/v1/health")
            if health.get("status") != "ok":
                raise ValueError("V1 health is not ok")
        result = run_cases(system, cases, repeats=args.repeats,
                           latency_target_ms=args.latency_target_ms)
        failures = sum(a["error"] for r in result["records"] for a in r["attempts"])
        comparison = compare(baseline["metrics"], result["metrics"]) if baseline else None
        result.update({"request_failures": failures, "comparison": comparison,
                       "status": "FAIL" if failures or (comparison and comparison["verdict"] == "REGRESSION")
                       else "MEASURED", "auto_accept": False})
        save_baseline(output, "smoke_mock" if args.mock else "v1_live", result,
                      mode="mock" if args.mock else "live_v1", captured_at=stamp,
                      dataset=str(dataset), dataset_sha256=hashlib.sha256(dataset_bytes).hexdigest(),
                      repeats=args.repeats, latency_target_ms=args.latency_target_ms,
                      base_url=None if args.mock else system.base_url, health=health,
                      limitations="Lexical scoring; not production readiness. Tool/policy/cost not inferred.")
        print(json.dumps({"output": str(output), "status": result["status"],
                          "metrics": result["metrics"], "request_failures": failures}, indent=2))
        return 1 if result["status"] == "FAIL" else 0
    except Exception as exc:
        print(f"Evaluation setup failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
