"""Save a GET-only, credential-safe extraction snapshot for operator review."""
import json
import hashlib
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[3]
run = Path(__file__).resolve().parent
document_id = "DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b"
values = dotenv_values(root / ".env", interpolate=False)
token = os.environ.get("NUSANTARA_ADMIN_TOKEN") or values.get("NUSANTARA_ADMIN_TOKEN")
if not token:
    raise SystemExit("Admin credential is not configured; no request sent.")

url = f"http://127.0.0.1:5180/v1/knowledge/pipeline/reviews/{document_id}"
request = urllib.request.Request(url, headers={"X-Admin-Token": token})
with urllib.request.urlopen(request, timeout=20) as response:
    if response.status != 200:
        raise SystemExit(f"Read-only review returned HTTP {response.status}.")
    body = json.loads(response.read())

extraction = body.get("extraction") or {}
blocks = body.get("extracted_blocks") or extraction.get("blocks") or []
markdown = (
    extraction.get("markdown")
    or extraction.get("full_document_text")
    or body.get("markdown")
    or body.get("full_document_text")
    or body.get("text")
    or ""
)
events = body.get("events") or []
trials = body.get("trials") or []
summary = {
    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    "live_detail_capture": True,
    "document_id": body.get("document_id"),
    "version_id": body.get("version_id"),
    "source_sha256": body.get("source_sha256"),
    "title": body.get("title"),
    "review_status": body.get("status"),
    "content_ok": body.get("content_ok"),
    "can_approve": body.get("can_approve"),
    "extraction_status": extraction.get("status") or body.get("extraction_status"),
    "page_count": extraction.get("page_count") or body.get("page_count") or len(body.get("pages") or []),
    "block_count": len(blocks),
    "live_text_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
    "trial_count": len(trials),
    "event_count": len(events),
    "event_kinds": dict(Counter(event.get("kind", "unknown") for event in events)),
    "approval_record_present": bool(body.get("approval")),
    "markdown": markdown,
}
(run / "live-sop-review-snapshot.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
lines = [
    "# Operator review — PIAK-03 Permohonan Data Pribadi",
    "",
    "This text was captured from the live review GET response for the exact version below. It is a read-only capture; no decision was submitted by this script.",
    "",
    f"- Document: `{summary['document_id']}`",
    f"- Extracted revision: `{summary['version_id']}`",
    f"- Source SHA-256: `{summary['source_sha256']}`",
    f"- Review state: `{summary['review_status']}`",
    f"- Content check: `{summary['content_ok']}`",
    f"- Approval eligibility: `{summary['can_approve']}`",
    f"- Extraction: `{summary['extraction_status']}`, {summary['page_count']} pages, {summary['block_count']} blocks",
    f"- Trials: {summary['trial_count']}; review events by kind: `{summary['event_kinds']}`",
    f"- Approval record present: `{summary['approval_record_present']}`",
    f"- Live text SHA-256: `{summary['live_text_sha256']}`",
    "",
    "## Extracted text",
    "",
    markdown or "(No markdown field was returned; see activity rows in the JSON snapshot.)",
    "",
]
(run / "live-sop-content-for-operator.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({
    "summary": {key: value for key, value in summary.items() if key != "markdown"},
    "response_fields": sorted(body),
    "extraction_fields": sorted(extraction),
    "extraction_field_types": {key: type(value).__name__ for key, value in extraction.items()},
}, ensure_ascii=False, indent=2))
print(f"Saved: {run / 'live-sop-content-for-operator.md'}")
