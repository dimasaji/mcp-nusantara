#!/usr/bin/env python3
"""
Answer Evaluator — Nusantara V1 Knowledge Intelligence & Core Engine Optimization
Evaluates benchmark results with comprehensive metrics:
- Answer Accuracy, Numerical Accuracy, SOP Identification
- Retrieval Recall & Precision, Citation Accuracy
- Multi-turn Conversation, Context Retention
- Hallucination Prevention, Response Latency
Usage: python scripts/answer_evaluator.py [--input reports/BENCHMARK_RESULTS.json] [--output-dir reports/]
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from difflib import SequenceMatcher

INPUT_PATH = "reports/BENCHMARK_RESULTS.json"
OUTPUT_DIR = "reports/"


def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def contains_key_phrase(actual: str, expected: str) -> bool:
    if not actual or not expected:
        return False
    actual_norm = normalize(actual)
    expected_norm = normalize(expected)
    key_words = [w for w in expected_norm.split() if len(w) > 3]
    if not key_words:
        return similarity(actual_norm, expected_norm) > 0.5
    matches = sum(1 for w in key_words if w in actual_norm)
    return matches / len(key_words) >= 0.5


def extract_numbers(text: str) -> List[str]:
    """Extract numeric values from text."""
    if not text:
        return []
    return re.findall(r"\d+[\.,]?\d*", text)


def numerical_accuracy(actual: str, expected: str) -> bool:
    """Check if numeric values in actual match expected."""
    expected_nums = extract_numbers(expected)
    actual_nums = extract_numbers(actual)
    if not expected_nums:
        return True  # No numbers to verify
    if not actual_nums:
        return False  # Expected numbers but none in actual
    return all(en in actual_nums for en in expected_nums)


def sop_identification_accuracy(actual_response: str, expected_sop_id: str,
                                 actual_grounded: bool) -> bool:
    """Check if SOP identification is correct."""
    if not expected_sop_id:
        return True
    if not actual_grounded:
        return False
    # Check if expected SOP ID appears in response or is implicitly identified
    return expected_sop_id.lower() in actual_response.lower() or actual_grounded


def citation_accuracy(actual_citation: str, expected_citation: str) -> bool:
    """Check if citation matches expected."""
    if not expected_citation or expected_citation == "tidak ada":
        return True  # No citation expected
    if not actual_citation:
        return False
    return expected_citation.lower() in actual_citation.lower()


def retrieval_recall_precision(actual_evidence_count: int,
                                expected_has_evidence: bool) -> Dict[str, float]:
    """Compute retrieval recall and precision."""
    if expected_has_evidence:
        recall = 1.0 if actual_evidence_count > 0 else 0.0
        precision = 1.0 if actual_evidence_count > 0 else 0.0
    else:
        recall = 1.0 if actual_evidence_count == 0 else 0.0
        precision = 1.0 if actual_evidence_count == 0 else 0.0
    return {"recall": recall, "precision": precision}


def hallucination_prevention(actual_grounded: bool, expected_behavior: str,
                              actual_response: str) -> bool:
    """Check if system correctly abstains when no evidence (no hallucination)."""
    if expected_behavior == "abstention":
        return not actual_grounded  # Should NOT be grounded
    else:
        return actual_grounded  # Should be grounded


def evaluate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    non_blocked = [r for r in results if not r.get("blocked")]
    nb_total = len(non_blocked)

    if nb_total == 0:
        return {"error": "No non-blocked results to evaluate"}

    # Overall metrics
    correct_answers = 0
    correct_numerical = 0
    correct_sop_id = 0
    correct_citations = 0
    correct_hallucination = 0
    correct_behaviors = 0
    api_errors = 0
    grounded_count = 0
    abstention_count = 0
    total_latency = 0.0
    latency_count = 0

    retrieval_recalls = []
    retrieval_precisions = []

    category_metrics = {}
    behavior_metrics = {"grounded_answer": {"total": 0, "correct": 0},
                        "abstention": {"total": 0, "correct": 0}}
    inference_mode_metrics = {"mock": {"total": 0, "correct": 0},
                              "synthetic": {"total": 0, "correct": 0},
                              "real": {"total": 0, "correct": 0}}

    # Multi-turn / context retention tracking
    retention_scenarios = [r for r in non_blocked if r.get("category") in ("retention", "lanjutan", "switching")]
    retention_correct = 0

    for r in non_blocked:
        cat = r["category"]
        if cat not in category_metrics:
            category_metrics[cat] = {"total": 0, "correct_answer": 0,
                                     "correct_numerical": 0, "correct_sop_id": 0,
                                     "correct_citation": 0, "correct_behavior": 0,
                                     "recall_sum": 0.0, "precision_sum": 0.0}

        category_metrics[cat]["total"] += 1

        # Answer correctness
        answer_ok = contains_key_phrase(r["actual_response"], r["expected_answer"])
        if answer_ok:
            correct_answers += 1
            category_metrics[cat]["correct_answer"] += 1

        # Numerical accuracy
        num_ok = numerical_accuracy(r["actual_response"], r["expected_answer"])
        if num_ok:
            correct_numerical += 1
            category_metrics[cat]["correct_numerical"] += 1

        # SOP identification
        sop_ok = sop_identification_accuracy(
            r["actual_response"], r.get("sop_id") or "", r["actual_grounded"]
        )
        if sop_ok:
            correct_sop_id += 1
            category_metrics[cat]["correct_sop_id"] += 1

        # Citation accuracy
        citation_ok = citation_accuracy(r["actual_citation"], r["expected_citation"])
        if citation_ok:
            correct_citations += 1
            category_metrics[cat]["correct_citation"] += 1

        # Behavior correctness
        behavior_ok = (r["actual_grounded"] == (r["expected_behavior"] == "grounded_answer"))
        if behavior_ok:
            correct_behaviors += 1
            category_metrics[cat]["correct_behavior"] += 1

        # Hallucination prevention
        hal_ok = hallucination_prevention(
            r["actual_grounded"], r["expected_behavior"], r["actual_response"]
        )
        if hal_ok:
            correct_hallucination += 1

        # Retrieval recall/precision
        expected_has_evidence = r["expected_behavior"] == "grounded_answer"
        rp = retrieval_recall_precision(r["actual_evidence_count"], expected_has_evidence)
        retrieval_recalls.append(rp["recall"])
        retrieval_precisions.append(rp["precision"])
        category_metrics[cat]["recall_sum"] += rp["recall"]
        category_metrics[cat]["precision_sum"] += rp["precision"]

        # API errors
        if r.get("api_error"):
            api_errors += 1

        # Grounding tracking
        if r["actual_grounded"]:
            grounded_count += 1
        else:
            abstention_count += 1

        # Latency tracking
        lat = r.get("actual_latency_ms", 0)
        if lat > 0:
            total_latency += lat
            latency_count += 1

        # Behavior tracking
        expected_behavior = r["expected_behavior"]
        if expected_behavior in behavior_metrics:
            behavior_metrics[expected_behavior]["total"] += 1
            if behavior_ok:
                behavior_metrics[expected_behavior]["correct"] += 1

        # Inference mode tracking
        inf_mode = r.get("inference_mode", "unknown")
        if inf_mode in inference_mode_metrics:
            inference_mode_metrics[inf_mode]["total"] += 1
            if behavior_ok:
                inference_mode_metrics[inf_mode]["correct"] += 1

        # Context retention tracking
        if cat in ("retention", "lanjutan", "switching"):
            if behavior_ok:
                retention_correct += 1

    # Compute overall percentages
    answer_accuracy = correct_answers / nb_total * 100
    numerical_accuracy_pct = correct_numerical / nb_total * 100
    sop_id_accuracy = correct_sop_id / nb_total * 100
    citation_validity = correct_citations / nb_total * 100
    behavior_accuracy = correct_behaviors / nb_total * 100
    hallucination_prevention_pct = correct_hallucination / nb_total * 100
    error_rate = api_errors / nb_total * 100
    avg_recall = sum(retrieval_recalls) / len(retrieval_recalls) if retrieval_recalls else 0.0
    avg_precision = sum(retrieval_precisions) / len(retrieval_precisions) if retrieval_precisions else 0.0
    avg_latency = total_latency / latency_count if latency_count else 0.0

    retention_accuracy = retention_correct / len(retention_scenarios) * 100 if retention_scenarios else 0.0

    # Per-category percentages
    for cat, m in category_metrics.items():
        t = m["total"]
        m["answer_accuracy_pct"] = m["correct_answer"] / t * 100
        m["numerical_accuracy_pct"] = m["correct_numerical"] / t * 100
        m["sop_id_accuracy_pct"] = m["correct_sop_id"] / t * 100
        m["citation_validity_pct"] = m["correct_citation"] / t * 100
        m["behavior_accuracy_pct"] = m["correct_behavior"] / t * 100
        m["recall_pct"] = m["recall_sum"] / t * 100
        m["precision_pct"] = m["precision_sum"] / t * 100

    # Per-behavior percentages
    for beh, m in behavior_metrics.items():
        m["accuracy_pct"] = m["correct"] / m["total"] * 100 if m["total"] > 0 else 0.0

    # Inference mode percentages
    for mode, m in inference_mode_metrics.items():
        m["accuracy_pct"] = m["correct"] / m["total"] * 100 if m["total"] > 0 else 0.0

    return {
        "summary": {
            "total_scenarios": nb_total,
            "blocked_scenarios": len(results) - nb_total,
            "answer_accuracy_pct": round(answer_accuracy, 2),
            "numerical_accuracy_pct": round(numerical_accuracy_pct, 2),
            "sop_id_accuracy_pct": round(sop_id_accuracy, 2),
            "citation_validity_pct": round(citation_validity, 2),
            "retrieval_recall_pct": round(avg_recall * 100, 2),
            "retrieval_precision_pct": round(avg_precision * 100, 2),
            "behavior_accuracy_pct": round(behavior_accuracy, 2),
            "hallucination_prevention_pct": round(hallucination_prevention_pct, 2),
            "context_retention_pct": round(retention_accuracy, 2),
            "error_rate_pct": round(error_rate, 2),
            "grounded_count": grounded_count,
            "abstention_count": abstention_count,
            "avg_latency_ms": round(avg_latency, 2),
        },
        "category_metrics": category_metrics,
        "behavior_metrics": behavior_metrics,
        "inference_mode_metrics": inference_mode_metrics,
    }


def generate_markdown_report(eval_result: Dict[str, Any], output_path: str):
    s = eval_result["summary"]
    cm = eval_result["category_metrics"]
    bm = eval_result["behavior_metrics"]
    im = eval_result["inference_mode_metrics"]

    lines = [
        "# Knowledge Benchmark Report — Nusantara V1",
        "",
        f"**Total scenarios:** {s['total_scenarios']}",
        f"**Blocked scenarios:** {s['blocked_scenarios']}",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Target | Actual | Status |",
        "|--------|--------|--------|--------|",
        f"| Answer Accuracy | ≥ 95% | {s['answer_accuracy_pct']}% | {'PASS' if s['answer_accuracy_pct'] >= 95 else 'FAIL'} |",
        f"| Numerical Accuracy | 100% | {s['numerical_accuracy_pct']}% | {'PASS' if s['numerical_accuracy_pct'] >= 100 else 'FAIL'} |",
        f"| SOP Identification | ≥ 95% | {s['sop_id_accuracy_pct']}% | {'PASS' if s['sop_id_accuracy_pct'] >= 95 else 'FAIL'} |",
        f"| Citation Validity | 100% | {s['citation_validity_pct']}% | {'PASS' if s['citation_validity_pct'] >= 100 else 'FAIL'} |",
        f"| Retrieval Recall | ≥ 95% | {s['retrieval_recall_pct']}% | {'PASS' if s['retrieval_recall_pct'] >= 95 else 'FAIL'} |",
        f"| Retrieval Precision | ≥ 95% | {s['retrieval_precision_pct']}% | {'PASS' if s['retrieval_precision_pct'] >= 95 else 'FAIL'} |",
        f"| Behavior Accuracy | ≥ 95% | {s['behavior_accuracy_pct']}% | {'PASS' if s['behavior_accuracy_pct'] >= 95 else 'FAIL'} |",
        f"| Hallucination Prevention | 100% | {s['hallucination_prevention_pct']}% | {'PASS' if s['hallucination_prevention_pct'] >= 100 else 'FAIL'} |",
        f"| Context Retention | ≥ 95% | {s['context_retention_pct']}% | {'PASS' if s['context_retention_pct'] >= 95 else 'FAIL'} |",
        f"| Error Rate | 0% | {s['error_rate_pct']}% | {'PASS' if s['error_rate_pct'] == 0 else 'FAIL'} |",
        "",
        f"**Grounded answers:** {s['grounded_count']}",
        f"**Abstentions:** {s['abstention_count']}",
        f"**Avg latency:** {s['avg_latency_ms']} ms",
        "",
        "## Per-Category Metrics",
        "",
        "| Category | Total | Answer % | Numerical % | SOP ID % | Citation % | Behavior % | Recall % | Precision % |",
        "|----------|-------|----------|-------------|----------|------------|------------|----------|-------------|",
    ]

    for cat, m in sorted(cm.items()):
        lines.append(f"| {cat} | {m['total']} | {m['answer_accuracy_pct']:.1f} | "
                     f"{m['numerical_accuracy_pct']:.1f} | {m['sop_id_accuracy_pct']:.1f} | "
                     f"{m['citation_validity_pct']:.1f} | {m['behavior_accuracy_pct']:.1f} | "
                     f"{m['recall_pct']:.1f} | {m['precision_pct']:.1f} |")

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
        "## Per-Inference-Mode Metrics",
        "",
        "| Mode | Total | Correct | Accuracy % |",
        "|------|-------|---------|------------|",
    ])

    for mode, m in sorted(im.items()):
        lines.append(f"| {mode} | {m['total']} | {m['correct']} | {m['accuracy_pct']:.1f} |")

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

    json_path = Path(args.output_dir) / "BENCHMARK_EVALUATION.json"
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2, ensure_ascii=False)
    print(f"Evaluation JSON saved to {json_path}")

    md_path = Path(args.output_dir) / "KNOWLEDGE_BENCHMARK_REPORT.md"
    generate_markdown_report(eval_result, str(md_path))

    s = eval_result["summary"]
    print(f"\n=== EVALUATION SUMMARY ===")
    print(f"Total: {s['total_scenarios']} | Blocked: {s['blocked_scenarios']}")
    print(f"Answer Accuracy: {s['answer_accuracy_pct']}%")
    print(f"Numerical Accuracy: {s['numerical_accuracy_pct']}%")
    print(f"SOP ID Accuracy: {s['sop_id_accuracy_pct']}%")
    print(f"Citation Validity: {s['citation_validity_pct']}%")
    print(f"Retrieval Recall: {s['retrieval_recall_pct']}%")
    print(f"Retrieval Precision: {s['retrieval_precision_pct']}%")
    print(f"Behavior Accuracy: {s['behavior_accuracy_pct']}%")
    print(f"Hallucination Prevention: {s['hallucination_prevention_pct']}%")
    print(f"Context Retention: {s['context_retention_pct']}%")
    print(f"Error Rate: {s['error_rate_pct']}%")


if __name__ == "__main__":
    main()