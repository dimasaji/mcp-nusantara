import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api import control_plane


def test_decision_request_accepts_ui_json_enum_string():
    body = control_plane.EvidenceDecisionInput.model_validate({
        "package_id": "evp_sha256_" + "a" * 64,
        "decision": "PASS",
        "notes": "",
    })
    assert body.decision is control_plane.HumanDecision.PASS


def _request(token=None):
    headers = [(b"host", b"127.0.0.1:8000"), (b"origin", b"http://127.0.0.1:5173"), (b"content-type", b"application/json")]
    if token is not None:
        headers.append((b"x-admin-token", token.encode()))
    return Request({"type": "http", "http_version": "1.1", "method": "POST", "scheme": "http",
        "path": "/v1/control-plane/decisions", "raw_path": b"/v1/control-plane/decisions", "query_string": b"",
        "headers": headers, "client": ("127.0.0.1", 4567), "server": ("127.0.0.1", 8000)})


def test_decision_api_requires_authorized_admin(monkeypatch, tmp_path):
    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "test-secret")
    monkeypatch.setenv("NUSANTARA_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(control_plane, "collect_review_package", lambda: {"package_id": "evp_sha256_" + "a" * 64, "pass_allowed": False, "blockers": [{"id": "AC1", "reason": "NOT_VERIFIED"}], "criteria": []})
    body = control_plane.EvidenceDecisionInput(package_id="evp_sha256_" + "a" * 64, decision=control_plane.HumanDecision.HOLD, notes="")
    with pytest.raises(HTTPException) as denied:
        control_plane.record_evidence_decision(body, _request())
    with pytest.raises(HTTPException) as invalid:
        control_plane.record_evidence_decision(body, _request("wrong"))
    allowed = control_plane.record_evidence_decision(body, _request("test-secret"))
    assert denied.value.status_code == 403
    assert invalid.value.status_code == 403
    assert allowed["reviewer_principal"] == "admin-token-holder"
    with pytest.raises(HTTPException) as blocked_pass:
        control_plane.record_evidence_decision(control_plane.EvidenceDecisionInput(package_id=body.package_id, decision=control_plane.HumanDecision.PASS, notes=""), _request("test-secret"))
    assert blocked_pass.value.status_code == 409


def test_decision_rejects_stale_or_client_forged_package(monkeypatch, tmp_path):
    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "test-secret")
    monkeypatch.setenv("NUSANTARA_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(control_plane, "collect_review_package", lambda: {"package_id": "evp_sha256_" + "b" * 64, "pass_allowed": True, "blockers": [], "criteria": []})
    request = _request("test-secret")
    with pytest.raises(HTTPException) as response:
        control_plane.record_evidence_decision(control_plane.EvidenceDecisionInput(package_id="evp_sha256_" + "c" * 64, decision=control_plane.HumanDecision.PASS, notes=""), request)
    assert response.value.status_code == 409
    assert not (tmp_path / "control_plane/evidence_decisions.jsonl").exists()


def test_legacy_snapshot_route_is_unchanged():
    assert any(route.path == "/v1/control-plane/snapshot" and "GET" in route.methods for route in control_plane.router.routes)
