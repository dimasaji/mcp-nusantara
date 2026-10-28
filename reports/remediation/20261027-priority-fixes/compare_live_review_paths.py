"""Read-only timing and provenance metadata probe; never emits secrets or trial text."""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "live-proxy-comparison.json"
DOC = "DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b"
TOKEN = os.environ.get("NUSANTARA_ADMIN_TOKEN") or dotenv_values(ROOT / ".env", interpolate=False).get("NUSANTARA_ADMIN_TOKEN")
if not TOKEN:
    raise SystemExit("Admin credential is not configured; no request sent.")

def get(name, url, review=False):
    started = time.monotonic()
    row = {"name": name, "url": url, "at_utc": datetime.now(timezone.utc).isoformat()}
    req = urllib.request.Request(url, headers={"X-Admin-Token": TOKEN} if review else {})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read()
            row.update(http_status=response.status, elapsed_ms=round((time.monotonic()-started)*1000),
                       content_length=len(body))
            if review:
                data = json.loads(body)
                ratings = {event.get("trial_id"): event for event in data.get("events", [])
                           if event.get("kind") == "rating"}
                row["review"] = {
                    "document_id": data.get("document_id"), "version_id": data.get("version_id"),
                    "source_sha256": data.get("source_sha256"), "status": data.get("status"),
                    "content_ok": data.get("content_ok"), "can_approve": data.get("can_approve"),
                    "source_available": data.get("source_available"),
                    "extraction_status": (data.get("extraction") or {}).get("status"),
                    "required_cases": data.get("required_cases"),
                    "approval_requirements": data.get("approval_requirements"),
                    "trials": [{"trial_id": t.get("trial_id"), "case_id": t.get("case_id"),
                                "principal": t.get("principal"), "created_at": t.get("created_at"),
                                "rating": ({"ok": t["rating"].get("ok"),
                                            "event_id": t["rating"].get("event_id"),
                                            "principal": t["rating"].get("principal"),
                                            "created_at": t["rating"].get("created_at")}
                                           if t.get("rating") else None)} for t in data.get("trials", [])],
                    "events": [{"event_id": e.get("event_id"), "kind": e.get("kind"),
                                "trial_id": e.get("trial_id"), "principal": e.get("principal"),
                                "created_at": e.get("created_at")} for e in data.get("events", [])],
                    "open_problem_count": len(data.get("problems", [])),
                    "approval_record_present": bool(data.get("approval")),
                }
    except urllib.error.HTTPError as exc:
        row.update(http_status=exc.code, elapsed_ms=round((time.monotonic()-started)*1000), error_type="HTTPError")
    except Exception as exc:
        row.update(http_status=None, elapsed_ms=round((time.monotonic()-started)*1000),
                   error_type=type(exc).__name__, reason_type=type(getattr(exc, "reason", None)).__name__)
    return row

base = f"/v1/knowledge/pipeline/reviews/{DOC}"
checks = [
    get("backend_health", "http://127.0.0.1:8000/health"),
    get("backend_review_direct", "http://127.0.0.1:8000" + base, review=True),
]
if "--direct-only" not in sys.argv:
    checks.extend([
        get("frontend_health_proxy", "http://127.0.0.1:5180/health"),
        get("frontend_review_proxy", "http://127.0.0.1:5180" + base, review=True),
    ])
result = {"captured_at_utc": datetime.now(timezone.utc).isoformat(), "observations": checks}
target = OUT if "--direct-only" not in sys.argv else OUT.with_name("live-review-requirements-after-restart.json")
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
