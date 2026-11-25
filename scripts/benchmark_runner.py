#!/usr/bin/env python3
"""
Benchmark Runner — Nusantara V1 Knowledge Intelligence & Core Engine Optimization
Executes GOLDEN_DATASET.json scenarios against Nusantara API (or mock) and records results.
Usage: python scripts/benchmark_runner.py [--mock] [--output reports/BENCHMARK_RESULTS.json]
"""

import json
import sys
import time
import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path for direct imports (mock mode)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

GOLDEN_DATASET_PATH = "reports/GOLDEN_DATASET.json"
DEFAULT_OUTPUT = "reports/BENCHMARK_RESULTS.json"


def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_api(question: str, session_id: str, model: str = "llama3.2:1b", stream: bool = False,
             base_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
    """Call Nusantara /v1/chat API."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "user_input": question,
        "session_id": session_id,
        "model": model,
        "stream": stream,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/v1/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {
            "error": True,
            "status_code": e.code,
            "message": e.read().decode("utf-8", errors="replace"),
            "session_id": session_id,
            "response": "",
            "grounding": {"grounded": False, "reason": "api_error", "evidence_count": 0},
            "evidence": [],
            "provider_status": "error",
            "latency_ms": 0,
        }
    except Exception as e:
        return {
            "error": True,
            "status_code": None,
            "message": str(e),
            "session_id": session_id,
            "response": "",
            "grounding": {"grounded": False, "reason": "api_error", "evidence_count": 0},
            "evidence": [],
            "provider_status": "error",
            "latency_ms": 0,
        }


def call_mock(question: str, session_id: str, dataset: List[Dict[str, Any]],
              model: str = "llama3.2:1b", stream: bool = False) -> Dict[str, Any]:
    """Mock API call using ground truth from dataset (for testing evaluator without live API)."""
    q_norm = (question or "").strip().lower()
    # Find matching scenario by question
    for scenario in dataset:
        sq = scenario.get("question") or ""
        if sq.strip().lower() == q_norm:
            expected = scenario["expected_answer"]
            behavior = scenario["expected_behavior"]
            citation = scenario["expected_citation"]
            grounded = behavior == "grounded_answer"
            return {
                "session_id": session_id,
                "response": expected,
                "grounding": {
                    "grounded": grounded,
                    "reason": "mock_ground_truth",
                    "evidence_count": 1 if grounded else 0,
                    "evidence_available": grounded,
                },
                "evidence": [{"chunk": expected, "score": 1.0}] if grounded else [],
                "provider_status": "mock",
                "latency_ms": 50,
                "trust": {"supports_claim": grounded, "confidence": 1.0 if grounded else 0.0},
                "understanding": {"intent": scenario.get("category", "unknown")},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    # No match found — abstention
    return {
        "session_id": session_id,
        "response": "Informasi tersebut belum tersedia secara cukup dalam knowledge base.",
        "grounding": {
            "grounded": False,
            "reason": "no_match",
            "evidence_count": 0,
            "evidence_available": False,
        },
        "evidence": [],
        "provider_status": "mock",
        "latency_ms": 50,
        "trust": {"supports_claim": False, "confidence": 0.0},
        "understanding": {"intent": "unknown"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_benchmark(dataset: List[Dict[str, Any]], mock: bool = False,
                  base_url: str = "http://127.0.0.1:8000") -> List[Dict[str, Any]]:
    results = []
    total = len(dataset)

    for i, scenario in enumerate(dataset, 1):
        question = scenario["question"]
        session_id = f"bench-{scenario['test_id']}-{uuid.uuid4().hex[:8]}"
        start = time.time()

        if mock:
            api_result = call_mock(question, session_id, dataset)
        else:
            api_result = call_api(question, session_id, base_url=base_url)

        latency_ms = (time.time() - start) * 1000

        result = {
            "test_id": scenario["test_id"],
            "split": scenario["split"],
            "category": scenario["category"],
            "document_id": scenario.get("document_id"),
            "sop_id": scenario.get("sop_id"),
            "question": question,
            "expected_answer": scenario["expected_answer"],
            "expected_evidence": scenario["expected_evidence"],
            "expected_citation": scenario["expected_citation"],
            "expected_behavior": scenario["expected_behavior"],
            "source_provenance": scenario["source_provenance"],
            "actual_response": api_result.get("response", ""),
            "actual_grounded": api_result.get("grounding", {}).get("grounded", False),
            "actual_evidence_count": api_result.get("grounding", {}).get("evidence_count", 0),
            "actual_citation": api_result.get("grounding", {}).get("reason", ""),
            "actual_provider_status": api_result.get("provider_status", "unknown"),
            "actual_latency_ms": round(latency_ms, 2),
            "api_error": api_result.get("error", False),
            "api_status_code": api_result.get("status_code"),
            "api_message": api_result.get("message", ""),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        status = "OK" if not result["api_error"] else "ERR"
        print(f"[{i:3d}/{total}] {scenario['test_id']} ({scenario['category']:15s}) {status} "
              f"latency={result['actual_latency_ms']}ms grounded={result['actual_grounded']}")

    return results


def save_results(results: List[Dict[str, Any]], output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path} ({len(results)} scenarios)")


def main():
    parser = argparse.ArgumentParser(description="Nusantara V1 Benchmark Runner")
    parser.add_argument("--mock", action="store_true", help="Use mock API (ground truth from dataset)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file path")
    parser.add_argument("--dataset", default=GOLDEN_DATASET_PATH, help="Dataset file path")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} scenarios from {args.dataset}")
    print(f"Mode: {'MOCK' if args.mock else 'LIVE API'} @ {args.base_url}")

    results = run_benchmark(dataset, mock=args.mock, base_url=args.base_url)
    save_results(results, args.output)

    # Quick summary
    total = len(results)
    errors = sum(1 for r in results if r["api_error"])
    grounded = sum(1 for r in results if r["actual_grounded"])
    avg_latency = sum(r["actual_latency_ms"] for r in results) / total if total else 0
    print(f"\n=== SUMMARY ===")
    print(f"Total: {total}")
    print(f"Errors: {errors}")
    print(f"Grounded: {grounded} ({grounded/total*100:.1f}%)")
    print(f"Avg latency: {avg_latency:.1f} ms")


if __name__ == "__main__":
    main()