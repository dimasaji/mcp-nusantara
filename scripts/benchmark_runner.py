#!/usr/bin/env python3
"""
Benchmark Runner — Nusantara V1 Knowledge Intelligence & Core Engine Optimization
Executes GOLDEN_DATASET.json scenarios against Nusantara API (MOCK, SYNTHETIC, or REAL INFERENCE).
Separates results by inference type. Marks blocked scenarios for missing dependencies.
Usage: python scripts/benchmark_runner.py [--mode mock|synthetic|real] [--output reports/]
"""

import json
import sys
import time
import argparse
import uuid
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

GOLDEN_DATASET_PATH = "reports/GOLDEN_DATASET.json"
DEFAULT_OUTPUT_DIR = "reports/"

# Dependency availability checks
OLLAMA_AVAILABLE = importlib.util.find_spec("ollama") is not None
INDOBERT_AVAILABLE = importlib.util.find_spec("transformers") is not None
DOCLING_AVAILABLE = importlib.util.find_spec("docling") is not None

# Check if Ollama service is reachable
def check_ollama_runtime(base_url: str = "http://127.0.0.1:11434") -> bool:
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

OLLAMA_RUNNING = check_ollama_runtime()


def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_mock(question: str, session_id: str, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MOCK inference: return ground truth from dataset without calling any model."""
    q_norm = (question or "").strip().lower()
    for scenario in dataset:
        sq = scenario.get("question") or ""
        if sq.strip().lower() == q_norm:
            expected = scenario["expected_answer"]
            behavior = scenario["expected_behavior"]
            grounded = behavior == "grounded_answer"
            return {
                "inference_type": "MOCK",
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
                "latency_ms": 1.0,
                "trust": {"supports_claim": grounded, "confidence": 1.0 if grounded else 0.0},
                "understanding": {"intent": scenario.get("category", "unknown")},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "blocked": False,
                "block_reason": None,
            }
    return {
        "inference_type": "MOCK",
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
        "latency_ms": 1.0,
        "trust": {"supports_claim": False, "confidence": 0.0},
        "understanding": {"intent": "unknown"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "blocked": False,
        "block_reason": None,
    }


def call_synthetic(question: str, session_id: str, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """SYNTHETIC inference: use backend components directly (FastAPI TestClient) without Ollama."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    try:
        resp = client.post("/v1/chat", json={
            "user_input": question,
            "session_id": session_id,
            "model": "mock",
            "stream": False,
        })
        data = resp.json()
        return {
            "inference_type": "SYNTHETIC",
            "session_id": session_id,
            "response": data.get("response", ""),
            "grounding": data.get("grounding", {"grounded": False, "reason": "synthetic", "evidence_count": 0}),
            "evidence": data.get("evidence", []),
            "provider_status": data.get("provider_status", "mock"),
            "latency_ms": data.get("latency_ms", 0),
            "trust": data.get("trust", {"supports_claim": False, "confidence": 0.0}),
            "understanding": data.get("understanding", {"intent": "unknown"}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blocked": False,
            "block_reason": None,
            "http_status": resp.status_code,
        }
    except Exception as e:
        return {
            "inference_type": "SYNTHETIC",
            "session_id": session_id,
            "response": "",
            "grounding": {"grounded": False, "reason": "synthetic_error", "evidence_count": 0},
            "evidence": [],
            "provider_status": "error",
            "latency_ms": 0,
            "trust": {"supports_claim": False, "confidence": 0.0},
            "understanding": {"intent": "unknown"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blocked": False,
            "block_reason": str(e),
            "http_status": None,
        }


def call_real(question: str, session_id: str, base_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
    """REAL INFERENCE: call the actual /v1/chat API endpoint."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "user_input": question,
        "session_id": session_id,
        "model": "llama3.2:1b",
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/v1/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return {
                "inference_type": "REAL",
                **json.loads(resp.read().decode("utf-8")),
                "http_status": resp.status,
                "blocked": False,
                "block_reason": None,
            }
    except urllib.error.HTTPError as e:
        return {
            "inference_type": "REAL",
            "error": True,
            "status_code": e.code,
            "message": e.read().decode("utf-8", errors="replace"),
            "session_id": session_id,
            "response": "",
            "grounding": {"grounded": False, "reason": "api_error", "evidence_count": 0},
            "evidence": [],
            "provider_status": "error",
            "latency_ms": 0,
            "trust": {"supports_claim": False, "confidence": 0.0},
            "understanding": {"intent": "unknown"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "http_status": e.code,
            "blocked": False,
            "block_reason": f"HTTP {e.code}",
        }
    except Exception as e:
        return {
            "inference_type": "REAL",
            "error": True,
            "status_code": None,
            "message": str(e),
            "session_id": session_id,
            "response": "",
            "grounding": {"grounded": False, "reason": "api_error", "evidence_count": 0},
            "evidence": [],
            "provider_status": "error",
            "latency_ms": 0,
            "trust": {"supports_claim": False, "confidence": 0.0},
            "understanding": {"intent": "unknown"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "http_status": None,
            "blocked": False,
            "block_reason": str(e),
        }


def check_blocked(scenario: Dict[str, Any]) -> tuple:
    """Check if a scenario should be marked BLOCKED due to missing dependencies."""
    category = scenario.get("category", "")
    sop_id = scenario.get("sop_id")

    # OCR/Docling dependent scenarios
    if category in ("di_luar_knowledge",) and sop_id == "CAPIL-01":
        if not DOCLING_AVAILABLE:
            return True, "Docling not installed (OCR extraction unavailable)"

    # Semantic/IndoBERT dependent scenarios
    if category in ("identitas_sop", "persyaratan", "prosedur", "durasi", "pelaksana", "output", "dasar_hukum"):
        if not INDOBERT_AVAILABLE:
            return True, "IndoBERT/transformers not installed (semantic retrieval unavailable)"

    # Ollama dependent scenarios (all grounded_answer scenarios need LLM)
    if scenario.get("expected_behavior") == "grounded_answer":
        if not OLLAMA_RUNNING:
            return True, "Ollama not running (LLM inference unavailable)"

    return False, None


def run_benchmark(dataset: List[Dict[str, Any]], mode: str = "mock",
                  base_url: str = "http://127.0.0.1:8000") -> List[Dict[str, Any]]:
    results = []
    total = len(dataset)
    blocked_count = 0

    print(f"Mode: {mode.upper()} @ {base_url}")
    print(f"Ollama running: {OLLAMA_RUNNING}, IndoBERT: {INDOBERT_AVAILABLE}, Docling: {DOCLING_AVAILABLE}")
    print()

    for i, scenario in enumerate(dataset, 1):
        question = scenario["question"]
        session_id = f"bench-{scenario['test_id']}-{uuid.uuid4().hex[:8]}"
        start = time.time()

        # Check if scenario should be blocked
        is_blocked, block_reason = check_blocked(scenario)

        if is_blocked:
            blocked_count += 1
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
                "inference_mode": mode,
                "actual_response": "",
                "actual_grounded": False,
                "actual_evidence_count": 0,
                "actual_citation": block_reason or "blocked",
                "actual_provider_status": "blocked",
                "actual_latency_ms": 0,
                "api_error": False,
                "api_status_code": None,
                "api_message": block_reason or "Scenario blocked",
                "blocked": True,
                "block_reason": block_reason,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }
            results.append(result)
            print(f"[{i:3d}/{total}] {scenario['test_id']} ({scenario['category']:15s}) BLOCKED: {block_reason}")
            continue

        # Run inference based on mode
        if mode == "mock":
            api_result = call_mock(question, session_id, dataset)
        elif mode == "synthetic":
            api_result = call_synthetic(question, session_id, dataset)
        elif mode == "real":
            api_result = call_real(question, session_id, base_url)
        else:
            raise ValueError(f"Unknown mode: {mode}")

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
            "inference_mode": mode,
            "actual_response": api_result.get("response", ""),
            "actual_grounded": api_result.get("grounding", {}).get("grounded", False),
            "actual_evidence_count": api_result.get("grounding", {}).get("evidence_count", 0),
            "actual_citation": api_result.get("grounding", {}).get("reason", ""),
            "actual_provider_status": api_result.get("provider_status", "unknown"),
            "actual_latency_ms": round(latency_ms, 2),
            "api_error": api_result.get("error", False),
            "api_status_code": api_result.get("status_code") or api_result.get("http_status"),
            "api_message": api_result.get("message", ""),
            "blocked": False,
            "block_reason": None,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        status = "OK" if not result["api_error"] else "ERR"
        print(f"[{i:3d}/{total}] {scenario['test_id']} ({scenario['category']:15s}) {status} "
              f"latency={result['actual_latency_ms']}ms grounded={result['actual_grounded']}")

    print(f"\nBlocked: {blocked_count}/{total}")
    return results


def save_results(results: List[Dict[str, Any]], output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path} ({len(results)} scenarios)")


def main():
    parser = argparse.ArgumentParser(description="Nusantara V1 Benchmark Runner")
    parser.add_argument("--mode", choices=["mock", "synthetic", "real"], default="mock",
                        help="Inference mode: mock (ground truth), synthetic (TestClient), real (live API)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--dataset", default=GOLDEN_DATASET_PATH, help="Dataset file path")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} scenarios from {args.dataset}")
    print(f"Dependency check: Ollama={OLLAMA_RUNNING}, IndoBERT={INDOBERT_AVAILABLE}, Docling={DOCLING_AVAILABLE}")

    results = run_benchmark(dataset, mode=args.mode, base_url=args.base_url)

    # Separate results by inference mode and blocked status
    mode_results = [r for r in results if not r.get("blocked")]
    blocked_results = [r for r in results if r.get("blocked")]
    mock_results = [r for r in mode_results if r.get("inference_mode") == "mock"]
    synthetic_results = [r for r in mode_results if r.get("inference_mode") == "synthetic"]
    real_results = [r for r in mode_results if r.get("inference_mode") == "real"]

    # Save separated results
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_results(results, str(output_dir / "BENCHMARK_RESULTS.json"))
    save_results(mock_results, str(output_dir / "BENCHMARK_RESULTS_MOCK.json"))
    save_results(synthetic_results, str(output_dir / "BENCHMARK_RESULTS_SYNTHETIC.json"))
    save_results(real_results, str(output_dir / "BENCHMARK_RESULTS_REAL.json"))
    save_results(blocked_results, str(output_dir / "BENCHMARK_RESULTS_BLOCKED.json"))

    # Summary
    total = len(results)
    errors = sum(1 for r in results if r.get("api_error"))
    grounded = sum(1 for r in results if r.get("actual_grounded") and not r.get("blocked"))
    non_blocked = [r for r in results if not r.get("blocked")]
    avg_latency = sum(r["actual_latency_ms"] for r in non_blocked) / len(non_blocked) if non_blocked else 0

    print(f"\n=== SUMMARY ===")
    print(f"Total: {total}")
    print(f"Blocked: {len(blocked_results)}")
    print(f"Errors: {errors}")
    print(f"Grounded (non-blocked): {grounded} ({grounded/len(non_blocked)*100:.1f}% of {len(non_blocked)})")
    print(f"Mock: {len(mock_results)} | Synthetic: {len(synthetic_results)} | Real: {len(real_results)}")
    print(f"Avg latency: {avg_latency:.1f} ms")


if __name__ == "__main__":
    main()