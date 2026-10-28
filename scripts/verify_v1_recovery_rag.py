"""Evaluate frozen project oracles against an isolated snapshot of the V1 store.

Never ingests or promotes production knowledge. Records missing/review-required
oracles separately from fixture retrieval and unchanged grounding guard checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
import gc
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.knowledge.grounding import EvidenceGroundingGuard
from app.knowledge.rag import RAG
from app.knowledge.store import SQLiteVectorStore


def run(output: Path) -> int:
    spec_path = ROOT / "app/evaluation/datasets/v1_recovery_oracle.json"
    raw = spec_path.read_bytes()
    spec = json.loads(raw)
    records = []
    guard = EvidenceGroundingGuard()
    with tempfile.TemporaryDirectory(prefix="v1-rag-", dir=ROOT / "reports") as temp:
        snapshot = Path(temp) / "knowledge.db"
        with closing(sqlite3.connect((ROOT / "data/knowledge/nusantara_knowledge.db").as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(snapshot)) as destination:
                source.backup(destination)
        rag = RAG(vector_store=SQLiteVectorStore(str(snapshot)))
        try:
            for case in spec["cases"]:
                status = case["oracle_status"]
                if status in {"MISSING", "REVIEW_REQUIRED"}:
                    records.append({"id": case["id"], "status": status,
                                    "runtime_knowledge_status": case.get("runtime_knowledge_status"),
                                    "reason": case.get("missing_reason", "Human source/version review and approved V1 knowledge are required")})
                    continue
                evidence = rag.query(case["question"], top_k=5).evidence_pack.evidence
                # Reproduce the route's unchanged relevance boundary.
                authoritative = [e for e in evidence if e.score >= .50]
                ids = [e.document_id for e in authoritative]
                wrong = sorted(set(ids) & set(case["negative_documents"]))
                if status == "NEGATIVE_CASE":
                    passed = not wrong
                    checks = {"unrelated_documents_not_authoritative": passed,
                              "no_evidence_claim_rejected": not guard.validate("Persyaratan wajib membawa surat ZYX.", []).grounded}
                else:
                    expected = case["expected_document"]
                    selected = [e for e in authoritative if e.document_id == expected]
                    text = " ".join(e.chunk for e in selected)
                    checks = {"expected_document_retrieved": expected in ids,
                              "required_evidence_present": all(q in text for q in case["required_evidence"]),
                              "unrelated_documents_not_authoritative": not wrong,
                              "source_answer_passes_guard": guard.validate(case["expected_answer"], selected, case["intent"]).grounded}
                    passed = all(checks.values())
                records.append({"id": case["id"], "status": "PASS" if passed else "FAIL", "checks": checks,
                                "authoritative_document_ids": ids, "wrong_domain_document_ids": wrong,
                                "retrieved": [{"document_id": e.document_id, "score": round(e.score, 6)} for e in evidence]})
            adversarial = []
            for answer in ("Biaya paspor Rp 999999.", "KTP selesai dalam 99 hari.",
                           "Persyaratan wajib membawa surat rahasia.", "Datang ke kantor ZYX di Jalan Fiktif 999."):
                result = guard.validate(answer, [{"chunk": "KTP-el adalah dokumen identitas penduduk."}])
                adversarial.append({"answer": answer, "rejected": not result.grounded, "reason": result.reason})
        finally:
            rag._embedding_adapter.stop()
            gc.collect()  # release SQLite context-manager connection cycles on Windows
    result = {"dataset": str(spec_path.relative_to(ROOT)), "dataset_sha256": hashlib.sha256(raw).hexdigest(),
              "mode": "real_indobert_snapshot_retrieval", "records": records, "adversarial": adversarial,
              "failures": sum(r["status"] == "FAIL" for r in records),
              "missing_or_review_required": sum(r["status"] in {"MISSING", "REVIEW_REQUIRED"} for r in records),
              "limitations": "Fixture retrieval and source-answer validation; no generated-answer correctness or production approval inferred"}
    result["status"] = "FAIL" if result["failures"] or not all(r["rejected"] for r in adversarial) else "VERIFY"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return int(result["status"] == "FAIL")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/V1_RECOVERY_RAG.json")
    raise SystemExit(run(parser.parse_args().output))
