from concurrent.futures import ThreadPoolExecutor

import pytest

from app.models.cost_ledger import CostGovernanceDenied, CostLedger


def make_ledger(path, budget="0.05", cap="0.03"):
    return CostLedger(
        path,
        budget_usd=budget,
        per_request_cap_usd=cap,
    )


def test_summary_uses_persisted_policy_and_unknown_reservations(tmp_path):
    ledger = make_ledger(tmp_path / 'ledger.sqlite3')
    ledger.reserve('paid', '0.03')
    ledger.settle('paid', '0.01')
    ledger.reserve('uncertain', '0.03')
    ledger.mark_unknown('uncertain')
    reopened = make_ledger(ledger.path)
    result = reopened.summary()
    assert result['actual_usd'] == '0.01'
    assert result['reserved_usd'] == '0.03'
    assert result['remaining_budget_usd'] == '0.01'
    assert result['budget_usd'] == '0.05'
    assert result['per_request_cap_usd'] == '0.03'
    assert result['provider_balance_usd'] is None
    assert result['input_tokens'] is None
    assert len(result['history']) == 2
    assert result['period']['start'] is not None


def test_reservation_persists_and_is_idempotent(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    ledger = make_ledger(path)

    assert ledger.reserve("req-1", "0.03") is True
    assert ledger.reserve("req-1", "0.03") is False
    assert ledger.status("req-1") == "reserved"

    reopened = make_ledger(path)
    assert reopened.status("req-1") == "reserved"


def test_cap_and_budget_fail_closed(tmp_path):
    ledger = make_ledger(tmp_path / "ledger.sqlite3")

    with pytest.raises(CostGovernanceDenied) as cap_error:
        ledger.reserve("too-large", "0.04")
    assert cap_error.value.code == "REQUEST_CAP_EXCEEDED"

    assert ledger.reserve("req-1", "0.03") is True
    with pytest.raises(CostGovernanceDenied) as budget_error:
        ledger.reserve("req-2", "0.03")
    assert budget_error.value.code == "BUDGET_EXCEEDED"


def test_zero_actual_cost_can_be_settled(tmp_path):
    ledger = make_ledger(tmp_path / "ledger.sqlite3")

    ledger.reserve("req-zero", "0.02")
    ledger.settle("req-zero", "0")
    assert ledger.status("req-zero") == "settled"
    assert ledger.reserved_usd == 0


def test_unknown_reservation_still_consumes_budget(tmp_path):
    ledger = make_ledger(tmp_path / "ledger.sqlite3")

    ledger.reserve("req-unknown", "0.03")
    ledger.mark_unknown("req-unknown")

    with pytest.raises(CostGovernanceDenied) as error:
        ledger.reserve("req-next", "0.03")
    assert error.value.code == "BUDGET_EXCEEDED"


def test_concurrent_reservations_cannot_exceed_budget(tmp_path):
    ledger_path = tmp_path / "ledger.sqlite3"

    def reserve_one(index):
        ledger = make_ledger(ledger_path)
        try:
            return ledger.reserve(f"concurrent-{index}", "0.02")
        except CostGovernanceDenied as error:
            return error.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(reserve_one, range(8)))

    assert results.count(True) == 2
    assert results.count("BUDGET_EXCEEDED") == 6


def test_missing_reservation_cannot_be_settled(tmp_path):
    ledger = make_ledger(tmp_path / "ledger.sqlite3")

    with pytest.raises(CostGovernanceDenied) as error:
        ledger.settle("missing", "0")
    assert error.value.code == "RESERVATION_NOT_FOUND"
