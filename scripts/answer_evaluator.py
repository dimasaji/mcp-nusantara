#!/usr/bin/env python3
"""
Answer Evaluator — Nusantara V1 Knowledge Intelligence & Core Engine Optimization
Evaluates benchmark results against expected answers, computes metrics per category.
Usage: python scripts/answer_evaluator.py [--input reports/BENCHMARK_RESULTS.json] [--output reports/]
"""

import json
import sys
import re
from pathlib import Path
from typing import Any, Dict, List
from difflib import SequenceMatcher

INPUT_PATH = "reports/BENCHMARK_RESULTS.json"
OUTPUT_DIR = "reports/"


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def similarity(a: str, b: str) -> float:
    """Compute text similarity ratio (0-1)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def contains_key_phrase(actual: str, expected: str) -> bool:
    """Check if actual answer contains key phrases from expected."""
    if not actual or not expected:
        return False
    actual_norm = normalize(actual)
    expected_norm = normalize(expected)
    # Split expected into key phrases (words > 3 chars)
    key_words = [w for w in expected_norm.split() if len(w) > 3]
    if not key_words:
        return similarity(actual_norm, expected_norm) > 0.5
    matches = sum(1 for w in key_words if w in actual_norm)
    return matches / len(key_words) >= 0.5


def evaluate_citation(actual_citation: str, expected_citation: str) -> bool:
    """Check if citation matches expected."""
    if not actual_citation or not expected_citation:
        return expected_citation == "tidak ada" or expected_citation == ""
    return expected_citation.lower() in actual_citation.lower()


def evaluate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    if total == 0:
        return {"error": "No results to evaluate"}

    # Overall metrics
    correct_answers = 0
    correct_citations = 0
    correct_behaviors = 0
    api_errors = 0
    grounded_count = 0
    abstention_count = 0

    category_metrics = {}
    behavior_metrics = {"grounded_answer": {"total": 0, "correct": 0},
                        "abstention": {"total": 0, "correct": 0}}

    for r in results:
        cat = r["category"]
        if cat not in category_metrics:
            category_metrics[cat] = {"total": 0, "correct_answer": 0,
                                     "correct_citation": 0, "correct_behavior": 0}

        category_metrics[cat]["total"] += 1

        # Answer correctness
        answer_ok = contains_key_phrase(r["actual_response"], r["expected_answer"])
        if answer_ok:
            correct_answers += 1
            category_metrics[cat]["correct_answer"] += 1

        # Citation correctness
        citation_ok = evaluate_citation(r["actual_citation"], r["expected_citation"])
        if citation_ok:
            correct_citations += 1
            category_metrics[cat]["correct_citation"] += 1

        # Behavior correctness
        behavior_ok = (r["actual_grounded"] == (r["expected_behavior"] == "grounded_answer"))
        if behavior_ok:
            correct_behaviors += 1
            category_metrics[cat]["correct_behavior"] += 1

        # API errors
        if r["api_error"]:
            api_errors += 1

        # Grounding tracking
        if r["actual_grounded"]:
            grounded_count += 1
        else:
            abstention_count += 1

        # Behavior tracking
        expected_behavior = r["expected_behavior"]
        if expected_behavior in behavior_metrics:
            behavior_metrics[expected_behavior]["total"] += 1
            if behavior_ok:
                behavior_metrics[expected_behavior]["correct"] += 1

    # Compute percentages
    answer_accuracy = correct_answers / total * 100
    citation_validity = correct_citations / total * 100
    behavior_accuracy = correct_behaviors / total * 100
    error_rate = api_errors / total * 100

    # Per-category percentages
    for cat, m in category_metrics.items():
        m["answer_accuracy_pct"] = m["correct_answer"] / m["total"] * 100
        m["citation_validity_pct"] = m["correct_citation"] / m["total"] * 100
        m["behavior_accuracy_pct"] = m["correct_behavior"] / m["total"] * 100

    # Per-behavior percentages
    for beh, m in behavior_metrics.items():
        m["accuracy_pct"] = m["correct"] / m["total"] * 100 if m["total"] > 0 else 0.0

    avg_latency = sum(r["actual_latency_ms"] for r in results) / total if total else 0

    return {
        "summary": {
            "total_scenarios": total,
            "answer_accuracy_pct": round(answer_accuracy, 2),
            "citation_validity_pct": round(citation_validity, 2),
            "behavior_accuracy_pct": round(behavior_accuracy, 2),
            "error_rate_pct": round(error_rate, 2),
            "grounded_count": grounded_count,
            "abstention_count": abstention_count,
            "avg_latency_ms": round(avg_latency, 2),
        },
        "category_metrics": category_metrics,
        "behavior_metrics": behavior_metrics,
    }


def generate_markdown_report(eval_result: Dict[str, Any], output_path: str):
    s = eval_result["summary"]
    cm = eval_result["category_metrics"]
    bm = eval_result["behavior_metrics"]

    lines = [
        "# Knowledge Benchmark Report — Nusantara V1",
        "",
        f"**Total scenarios:** {s['total_scenarios']}",
        f"**Answer accuracy:** {s['answer_accuracy_pct']}%",
        f"**Citation validity:** {s['citation_validity_pct']}%",
        f"**Behavior accuracy:** {s['behavior_accuracy_pct']}%",
        f"**Error rate:** {s['error_rate_pct']}%",
        f"**Grounded answers:** {s['grounded_count']}",
        f"**Abstentions:** {s['abstention_count']}",
        f"**Avg latency:** {s['avg_latency_ms']} ms",
        "",
        "## Per-Category Metrics",
        "",
        "| Category | Total | Answer Acc % | Citation Val % | Behavior Acc % |",
        "|----------|-------|--------------|----------------|----------------|",
    ]

    for cat, m in sorted(cm.items()):
        lines.append(f"| {cat} | {m['total']} | {m['answer_accuracy_pct']:.1f} | "
                     f"{m['citation_validity_pct']:.1f} | {m['behavior_accuracy_pct']:.1f} |")

    lines.extend([
        "",
        "## Per-Behavior Metrics",
        "",
        "| Behavior | Total | Correct | Accuracy % |",
        "|----------|-------|---------|------------|",
    ])

    for beh, m in sorted(bm.items()):
        lines.append(f"| {beh} | {m['total']} | {m['correct']} | {m['accuracy_pct']:.1f} |")

    lines.extend([
        "",
        "## Targets (Master Engineering Contract)",
        "| Metric | Target | Actual | Status |",
        "|--------|--------|--------|--------|",
        f"| Answer Accuracy | ≥ 95% | {s['answer_accuracy_pct']}% | {'PASS' if s['answer_accuracy_pct'] >= 95 else 'FAIL'} |",
        f"| Citation Validity | 100% | {s['citation_validity_pct']}% | {'PASS' if s['citation_validity_pct'] >= 100 else 'FAIL'} |",
        f"| Behavior Accuracy | ≥ 95% | {s['behavior_accuracy_pct']}% | {'PASS' if s['behavior_accuracy_pct'] >= 95 else 'FAIL'} |",
        f"| New Regression | 0 | {s['error_rate_pct']}% | {'PASS' if s['error_rate_pct'] == 0 else 'FAIL'} |",
    ])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report saved to {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Nusantara V1 Answer Evaluator")
    parser.add_argument("--input", default=INPUT_PATH, help="Input benchmark results file")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        results = json.load(f)

    eval_result = evaluate(results)

    # Save JSON
    json_path = Path(args.output_dir) / "BENCHMARK_EVALUATION.json"
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2, ensure_ascii=False)
    print(f"Evaluation JSON saved to {json_path}")

    # Save markdown
    md_path = Path(args.output_dir) / "KNOWLEDGE_BENCHMARK_REPORT.md"
    generate_markdown_report(eval_result, str(md_path))

    # Print summary
    s = eval_result["summary"]
    print(f"\n=== EVALUATION SUMMARY ===")
    print(f"Total: {s['total_scenarios']}")
    print(f"Answer Accuracy: {s['answer_accuracy_pct']}%")
    print(f"Citation Validity: {s['citation_validity_pct']}%")
    print(f"Behavior Accuracy: {s['behavior_accuracy_pct']}%")
    print(f"Error Rate: {s['error_rate_pct']}%")


if __name__ == "__main__":
    main()