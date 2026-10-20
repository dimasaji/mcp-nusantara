
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ============================================================
# NUSANTARA V1 - RETRIEVAL EVIDENCE
# Local tests only. Paid provider tests are deliberately disabled.
# ============================================================

$Root = (Get-Location).Path
$Schemas = Join-Path $Root 'app\knowledge\schemas.py'
$EvidenceModule = Join-Path $Root 'app\knowledge\retrieval_evidence.py'
$EvidenceTest = Join-Path $Root 'tests\test_retrieval_evidence_persistence.py'
$EvidenceDir = Join-Path $Root 'data\evidence'
$EvidenceFile = Join-Path $EvidenceDir 'retrieval-receipts.jsonl'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

if (-not (Test-Path (Join-Path $Root '.git'))) {
    throw "Bukan root repo Git: $Root"
}
if (-not (Test-Path $Schemas)) {
    throw "File tidak ditemukan: $Schemas"
}
if (-not (Test-Path (Join-Path $Root 'tests'))) {
    throw 'Folder tests tidak ditemukan.'
}

$GitBranch = git branch --show-current
if ($LASTEXITCODE -ne 0) { throw 'Tidak dapat membaca status Git.' }

Write-Host "Repo       : $Root"
Write-Host "Branch     : $GitBranch"
Write-Host 'Paid tests : DISABLED' -ForegroundColor Green

# Select the repo virtual environment if available.
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
    throw 'Python tidak ditemukan. Aktifkan environment Python Nusantara terlebih dahulu.'
}

# The receipt module and test are additive. Never overwrite existing files.
$ExistingModule = Test-Path $EvidenceModule
$ExistingTest = Test-Path $EvidenceTest
$CurrentSchemas = Get-Content $Schemas -Raw

if ($ExistingModule -and $CurrentSchemas -notmatch 'persist_retrieval_receipt') {
    throw "Modul sudah ada tetapi belum terhubung. Periksa manual: $EvidenceModule"
}
if ($ExistingTest) {
    throw "Tes sudah ada; skrip berhenti agar tidak menimpa: $EvidenceTest"
}

# Backup before touching schemas.py.
$Backup = "$Schemas.backup-$Stamp"
Copy-Item $Schemas $Backup
Write-Host "Backup     : $Backup"

# ------------------------------------------------------------
# A. Persistent receipt writer: append-only JSONL + SHA-256
# ------------------------------------------------------------

if (-not $ExistingModule) {
@'
"""Persistent local storage for effective RAG receipts.

Stores receipt metadata, not the user's raw query or retrieved text.
Each line is independently SHA-256 verifiable.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def receipt_path() -> Path:
    configured = os.environ.get("NUSANTARA_RETRIEVAL_EVIDENCE_PATH")
    if configured:
        return Path(configured).expanduser().resolve()

    # app/knowledge/retrieval_evidence.py -> repository root
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "evidence" / "retrieval-receipts.jsonl"


def persist_retrieval_receipt(snapshot: dict[str, Any]) -> dict[str, str]:
    """Append one receipt record and fsync it before returning."""
    if not isinstance(snapshot, dict):
        raise TypeError("Receipt snapshot must be a dictionary")

    invocation_id = snapshot.get("invocation_id")
    if not isinstance(invocation_id, str) or not invocation_id.strip():
        raise ValueError("Receipt invocation_id is missing")

    record: dict[str, Any] = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "receipt": snapshot,
    }
    record["record_sha256"] = hashlib.sha256(
        _canonical_json(record).encode("utf-8")
    ).hexdigest()

    path = receipt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = _canonical_json(record) + "\n"

    # The service is configured for one Uvicorn worker. The lock also
    # prevents concurrent threads in this process from interleaving writes.
    with _LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())

    return {
        "path": str(path),
        "record_sha256": record["record_sha256"],
    }


def verify_receipt_record(record: dict[str, Any]) -> bool:
    """Verify the record hash; this does not prove source authenticity."""
    if not isinstance(record, dict):
        return False
    supplied = record.get("record_sha256")
    if not isinstance(supplied, str):
        return False
    payload = {key: value for key, value in record.items()
               if key != "record_sha256"}
    expected = hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
    return supplied == expected
'@ | Set-Content -Path $EvidenceModule -Encoding utf8
    Write-Host 'Created    : app\knowledge\retrieval_evidence.py'
}

# ------------------------------------------------------------
# B. Connect the existing receipt publisher to persistent storage
# ------------------------------------------------------------

if ($CurrentSchemas -notmatch 'persist_retrieval_receipt') {
    $Pattern = '(?ms)^def _log_receipt\(receipt: EffectiveRAGProfile\) -> None:\r?\n.*?(?=^def publish_rag_profile\()'

    $Matches = [regex]::Matches($CurrentSchemas, $Pattern)
    if ($Matches.Count -ne 1) {
        throw 'Bentuk _log_receipt tidak cocok. Tidak ada patch yang dipaksakan; backup sudah dibuat.'
    }

    $Replacement = @'
def _log_receipt(receipt: EffectiveRAGProfile) -> None:
    snapshot = receipt.snapshot()
    log_event('effective_rag_profile', profile=snapshot)
    try:
        from app.knowledge.retrieval_evidence import persist_retrieval_receipt
        persist_retrieval_receipt(snapshot)
    except Exception as exc:
        # Do not log query text, retrieved content, or exception details.
        log_event(
            'effective_rag_profile_persistence_failed',
            invocation_id=snapshot.get('invocation_id'),
            exception_type=type(exc).__name__,
        )


'@

    $UpdatedSchemas = [regex]::Replace(
        $CurrentSchemas, $Pattern, $Replacement, 1
    )
    if ($UpdatedSchemas -eq $CurrentSchemas) {
        throw 'Patch schemas.py tidak menghasilkan perubahan.'
    }

    Set-Content -Path $Schemas -Value $UpdatedSchemas -Encoding utf8
    Write-Host 'Updated    : app\knowledge\schemas.py'
}
else {
    Write-Host 'Publisher  : persistent writer already connected'
}

# ------------------------------------------------------------
# C. Local persistence and integrity tests
# ------------------------------------------------------------

@'
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
'@ | Set-Content -Path $EvidenceTest -Encoding utf8
Write-Host 'Created    : tests\test_retrieval_evidence_persistence.py'

# ------------------------------------------------------------
# D. Local tests only; no provider calls are intentionally made
# ------------------------------------------------------------

$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'

Write-Host "`n=== LOCAL RECEIPT TESTS ==="
& $Python -m pytest -q $EvidenceTest .\tests\test_effective_rag_profile.py
$LocalTestExit = $LASTEXITCODE
Write-Host "Local test exit code: $LocalTestExit"

# ------------------------------------------------------------
# E. Runtime verification: only use an already-running local service
# ------------------------------------------------------------

Write-Host "`n=== LOCAL RUNTIME CHECK ==="
$BaseUrl = 'http://127.0.0.1:8000'
$RuntimeVerified = $false
$RuntimeReason = 'NOT_VERIFIED'

try {
    $Health = Invoke-RestMethod `
        -Uri "$BaseUrl/v1/health/detail" `
        -Method Get -TimeoutSec 8

    Write-Host 'Health endpoint responded.'
    $BeforeCount = 0
    if (Test-Path $EvidenceFile) {
        $BeforeCount = @(Get-Content $EvidenceFile).Count
    }

    $Payload = @{
        session_id = "retrieval-evidence-$Stamp"
        user_input = 'Jelaskan perbedaan KTP elektronik dan paspor berdasarkan pengetahuan yang tersedia.'
        stream = $false
    } | ConvertTo-Json -Depth 5

    try {
        $Chat = Invoke-RestMethod `
            -Uri "$BaseUrl/v1/chat" `
            -Method Post `
            -ContentType 'application/json' `
            -Body $Payload `
            -TimeoutSec 180
    }
    catch {
        Write-Warning "Request chat gagal: $($_.Exception.Message)"
        $Chat = $null
    }

    if (Test-Path $EvidenceFile) {
        $Lines = @(Get-Content $EvidenceFile)
        $NewLines = @()
        if ($Lines.Count -gt $BeforeCount) {
            $NewLines = $Lines | Select-Object -Skip $BeforeCount
        }

        $Records = @()
        foreach ($Line in $NewLines) {
            try { $Records += ($Line | ConvertFrom-Json) } catch {}
        }

        $V1Receipts = @(
            $Records | Where-Object {
                $_.receipt.consumer -eq 'V1_CHAT' -and
                $_.receipt.invocation_id
            }
        )

        if ($Chat -and $V1Receipts.Count -gt 0) {
            $RuntimeVerified = $true
            $RuntimeReason = 'RECEIPT_OBSERVED_FOR_V1_CHAT'
            Write-Host "New V1_CHAT receipt(s): $($V1Receipts.Count)" -ForegroundColor Green
        }
        else {
            Write-Warning 'Belum ditemukan receipt V1_CHAT baru yang dapat dikaitkan dengan request ini.'
        }
    }
    else {
        Write-Warning 'Receipt file belum dibuat oleh runtime.'
    }
}
catch {
    $RuntimeReason = 'LOCAL_SERVICE_UNAVAILABLE_OR_HEALTH_CHECK_FAILED'
    Write-Warning 'Runtime lokal tidak tersedia atau health check gagal. Skrip tidak akan memulai service otomatis.'
}

# ------------------------------------------------------------
# F. Summary. Do not equate test success with runtime PASS.
# ------------------------------------------------------------

Write-Host "`n================ HASIL ================"
Write-Host "Local tests exit : $LocalTestExit"
Write-Host "Runtime observed : $RuntimeVerified"
Write-Host "Runtime status   : $RuntimeReason"
Write-Host "Receipt file     : $EvidenceFile"
Write-Host 'Paid provider    : NOT RUN'
Write-Host 'Control Plane PASS: NOT AUTOMATICALLY GRANTED'

if ($LocalTestExit -ne 0) {
    throw 'Tes lokal gagal. Jangan lanjut ke tes provider berbayar.'
}

if (-not $RuntimeVerified) {
    Write-Warning 'Tes lokal lulus, tetapi verifikasi runtime belum lengkap.'
}
