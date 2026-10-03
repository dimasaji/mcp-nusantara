#!/usr/bin/env python3
"""Jalankan dataset evaluasi terhadap sistem yang Anda sambungkan.
Default: SISTEM MOCK deterministik = smoke test harness, BUKAN baseline V1 asli.
Untuk baseline V1 nyata, ganti `system()` agar memanggil /v1/chat pada mesin Anda."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.evaluation import EvalCase, run_cases, save_baseline  # noqa: E402


def system(query: str) -> dict:  # ganti dengan pemanggilan sistem nyata
    if "ktp" in query:
        return {"answer": "Biaya KTP gratis", "evidence": ["Biaya KTP gratis"], "retrieved_doc_ids": ["ktp"]}
    if "hitung" in query:
        return {"answer": "36", "tool_called": "calculator"}
    if "gaji" in query:
        return {"answer": "Perlu peninjauan manusia", "policy_decision": "REQUIRE_HUMAN"}
    return {"answer": "Halo, baik.", "tool_called": None}


if __name__ == "__main__":
    cases = [EvalCase(**c) for c in json.loads((ROOT / "app/evaluation/datasets/smoke_id.json").read_text())]
    res = run_cases(system, cases, repeats=2)
    out = ROOT / "app/evaluation/baselines/smoke_mock.json"
    save_baseline(out, "smoke_mock", res, note="MOCK - bukan baseline V1")
    print(json.dumps(res, indent=2))
