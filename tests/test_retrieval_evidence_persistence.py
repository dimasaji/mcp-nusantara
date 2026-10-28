import json

from app.knowledge.retrieval_evidence import (
    persist_retrieval_receipt,
    receipt_path,
    verify_receipt_record,
)


def test_receipt_is_persisted_and_hash_verifies(tmp_path, monkeypatch):
    target = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("NUSANTARA_RETRIEVAL_EVIDENCE_PATH", str(target))

    receipt = {
        "invocation_id": "test-invocation-001",
        "consumer": "V1_CHAT",
        "status": "COMPLETED",
    }

    result = persist_retrieval_receipt(receipt)

    assert result["path"] == str(target)
    assert target.exists()

    records = [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 1
    assert records[0]["receipt"] == receipt
    assert verify_receipt_record(records[0])


def test_tampered_receipt_fails_integrity_check(tmp_path, monkeypatch):
    target = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("NUSANTARA_RETRIEVAL_EVIDENCE_PATH", str(target))

    persist_retrieval_receipt({
        "invocation_id": "test-invocation-002",
        "consumer": "V1_CHAT",
        "status": "COMPLETED",
    })

    record = json.loads(target.read_text(encoding="utf-8").splitlines()[0])
    record["receipt"]["status"] = "FAILED"

    assert not verify_receipt_record(record)


def test_receipt_requires_invocation_id(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "NUSANTARA_RETRIEVAL_EVIDENCE_PATH",
        str(tmp_path / "receipts.jsonl"),
    )

    try:
        persist_retrieval_receipt({"consumer": "V1_CHAT"})
    except ValueError:
        pass
    else:
        raise AssertionError("Receipt without invocation_id was accepted")
