"""Phase 20 - laporan kesiapan rilis. NOT_RUN pada check wajib => CONDITIONAL, bukan PASS."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    critical: bool = False   # FAIL pada check kritis => BLOCK RELEASE


def verdict(checks: list[Check]) -> str:
    if any(c.status == FAIL and c.critical for c in checks):
        return "FAIL"      # BLOCK RELEASE
    if any(c.status == FAIL for c in checks) or any(c.status == NOT_RUN for c in checks):
        return "CONDITIONAL"
    return "PASS"


def render(version: str, checks: list[Check], baseline_note: str) -> str:
    v = verdict(checks)
    def cell(value):
        return str(value).replace('|', '\\|').replace('\r', '').replace('\n', '<br>')
    rows = "\n".join(f"| {cell(c.name)} | {c.status}{' (kritis)' if c.critical and c.status == FAIL else ''} | {cell(c.detail)} |"
                     for c in checks)
    block = "\n**BLOCK RELEASE** - ada check wajib yang gagal; lihat bukti di bawah.\n" if v == "FAIL" else ""
    return (f"# RELEASE_READINESS_REPORT\n\nVersi kandidat: {version}\nTanggal: {datetime.now(timezone.utc).isoformat()}\n"
            f"Status: **{v}**\n{block}\nBaseline V1: {baseline_note}\n\n| Check | Status | Detail |\n|---|---|---|\n{rows}\n\n"
            "PASS berarti seluruh check dijalankan dan lulus. NOT_RUN berarti check belum dapat dijalankan di lingkungan ini.\n")
