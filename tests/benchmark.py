"""Performance benchmark untuk Nusantara V1 Lean Intelligence Engine.

Mengukur latensi per mode jawaban (faktual struktural, sintesis fallback,
abstensi) dan menyimpan hasil ke reports/benchmark.json.
"""

import json
import time
from pathlib import Path

import lia_engine as L

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

QUERIES = [
    ("Apa layanan KTP-el?", "faktual"),
    ("Apa persyaratan pembuatan KTP-el?", "faktual"),
    ("Bagaimana prosedur pembuatan KTP-el?", "faktual"),
    ("Berapa lama waktu penyelesaian KTP-el?", "faktual"),
    ("Siapa pelaksana layanan KTP-el?", "faktual"),
    ("Apa output layanan KTP-el?", "faktual"),
    ("Dasar hukum layanan KTP-el?", "faktual"),
    ("Dan bagaimana caranya?", "lanjutan"),
    ("Apa itu kuliner khas Tangerang?", "abstensi"),
]


def bench(engine, repeats=5):
    results = {}
    for query, mode in QUERIES:
        times = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            engine.process(query, "bench-sesi")
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        results[query] = {
            "mode": mode,
            "min_ms": round(times[0], 2),
            "p50_ms": round(times[len(times) // 2], 2),
            "max_ms": round(times[-1], 2),
        }
    return results


def main():
    engine = L.LiaEngine()
    results = bench(engine, repeats=5)
    all_lat = []
    for v in results.values():
        all_lat.extend([v["min_ms"], v["p50_ms"], v["max_ms"]])
    summary = {
        "overall_p50_ms": round(sum(v["p50_ms"] for v in results.values()) / len(results), 2),
        "overall_max_ms": round(max(v["max_ms"] for v in results.values()), 2),
        "target_factual_ms": 2000,
        "target_followup_ms": 3000,
        "target_synthesis_ms": 30000,
    }
    report = {"summary": summary, "queries": results}
    out = REPORT_DIR / "benchmark.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Tulis {out}")


if __name__ == "__main__":
    main()
