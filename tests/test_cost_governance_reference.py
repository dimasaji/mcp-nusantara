"""Isolated reference tests for Cost Governance Guard.
This file is a test-only prototype, not production enforcement.
No provider, network, credentials, or database are used.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from threading import Lock


MILLION = Decimal("1000000")
CENT = Decimal("0.01")


class Denied(RuntimeError):
    pass


@dataclass(frozen=True)
class Price:
    model: str
    input_per_million: Decimal
    output_per_million: Decimal
    version: str = "fixture-v1"
    valid: bool = True


@dataclass(frozen=True)
class Policy:
    budget: Decimal
    per_request_cap: Decimal
    currency: str = "USD"


class FakeLedger:
    """Thread-safe in-memory ledger; not persistent production storage."""

    def __init__(self, budget):
        self.budget = Decimal(budget)
        self._lock = Lock()
        self._reservations = {}
        self._unknown = set()

    def reserve(self, request_id, amount):
        amount = Decimal(amount)
        if not request_id or not amount.is_finite() or amount <= 0:
            raise Denied("INVALID_RESERVATION")

        with self._lock:
            if request_id in self._reservations:
                if self._reservations[request_id] != amount:
                    raise Denied("IDEMPOTENCY_CONFLICT")
                return False

            reserved = sum(self._reservations.values(), Decimal("0"))
            if reserved + amount > self.budget:
                raise Denied("BUDGET_EXCEEDED")

            self._reservations[request_id] = amount
            return True

    def mark_unknown(self, request_id):
        with self._lock:
            if request_id not in self._reservations:
                raise Denied("RESERVATION_NOT_FOUND")
            self._unknown.add(request_id)

    @property
    def reserved(self):
        with self._lock:
            return sum(self._reservations.values(), Decimal("0"))

    def is_unknown(self, request_id):
        with self._lock:
            return request_id in self._unknown


class ReferenceGuard:
    """Specification prototype used only by this isolated test file."""

    def __init__(self, policy, ledger, prices):
        self.policy = policy
        self.ledger = ledger
        self.prices = prices

    def authorize(self, request_id, model, input_tokens, max_output_tokens):
        if not isinstance(self.policy, Policy):
            raise Denied("POLICY_UNAVAILABLE")
        if self.policy.currency != "USD":
            raise Denied("CURRENCY_UNSUPPORTED")
        if model not in self.prices:
            raise Denied("PRICE_UNAVAILABLE")

        price = self.prices[model]
        if not price.valid or price.model != model or not price.version:
            raise Denied("PRICE_UNVERIFIED")

        if (type(input_tokens) is not int or input_tokens < 0 or
                type(max_output_tokens) is not int or max_output_tokens <= 0):
            raise Denied("INVALID_TOKEN_ESTIMATE")

        try:
            input_cost = (
                Decimal(input_tokens) * price.input_per_million / MILLION
            )
            output_cost = (
                Decimal(max_output_tokens) * price.output_per_million / MILLION
            )
            estimate = (input_cost + output_cost).quantize(
                CENT, rounding=ROUND_CEILING
            )
        except (InvalidOperation, TypeError, ValueError):
            raise Denied("INVALID_COST_ESTIMATE")

        if (not estimate.is_finite() or estimate <= 0 or
                price.input_per_million < 0 or price.output_per_million < 0):
            raise Denied("INVALID_COST_ESTIMATE")
        if estimate > self.policy.per_request_cap:
            raise Denied("REQUEST_CAP_EXCEEDED")

        self.ledger.reserve(request_id, estimate)
        return {"authorized": True, "reserved": estimate,
                "price_version": price.version}


def make_guard(budget="2.00", cap="1.00", price=None):
    model = "fixture/model"
    price = price or Price(
        model, Decimal("1.00"), Decimal("2.00")
    )
    ledger = FakeLedger(Decimal(budget))
    guard = ReferenceGuard(
        Policy(Decimal(budget), Decimal(cap)),
        ledger, {model: price}
    )
    return guard, ledger, model


def test_authorized_request_reserves_before_any_dispatch():
    guard, ledger, model = make_guard()
    result = guard.authorize("r1", model, 1000, 1000)
    assert result["authorized"] is True
    assert result["reserved"] == Decimal("0.01")
    assert ledger.reserved == Decimal("0.01")
    # No transport exists in this test-only prototype.


def test_request_cap_rejects_before_reservation():
    guard, ledger, model = make_guard(cap="0.005")
    try:
        guard.authorize("r1", model, 1000, 1000)
        assert False, "request should have been denied"
    except Denied as exc:
        assert str(exc) == "REQUEST_CAP_EXCEEDED"
    assert ledger.reserved == 0


def test_missing_or_unverified_price_fails_closed():
    model = "fixture/model"
    ledger = FakeLedger(Decimal("10"))
    guard = ReferenceGuard(
        Policy(Decimal("10"), Decimal("10")), ledger, {}
    )
    try:
        guard.authorize("r1", model, 1, 1)
        assert False, "missing price should be denied"
    except Denied as exc:
        assert str(exc) == "PRICE_UNAVAILABLE"
    assert ledger.reserved == 0

    invalid = Price(model, Decimal("1"), Decimal("1"), valid=False)
    guard.prices[model] = invalid
    try:
        guard.authorize("r2", model, 1, 1)
        assert False, "unverified price should be denied"
    except Denied as exc:
        assert str(exc) == "PRICE_UNVERIFIED"
    assert ledger.reserved == 0


def test_budget_exhaustion_rejects_without_reservation():
    guard, ledger, model = make_guard(budget="0.01", cap="1.00")
    guard.authorize("r1", model, 1000, 1000)
    try:
        guard.authorize("r2", model, 1000, 1000)
        assert False, "second request should exceed budget"
    except Denied as exc:
        assert str(exc) == "BUDGET_EXCEEDED"
    assert ledger.reserved == Decimal("0.01")


def test_duplicate_reservation_is_idempotent():
    ledger = FakeLedger(Decimal("1.00"))
    assert ledger.reserve("same-id", Decimal("0.20")) is True
    assert ledger.reserve("same-id", Decimal("0.20")) is False
    assert ledger.reserved == Decimal("0.20")
    try:
        ledger.reserve("same-id", Decimal("0.30"))
        assert False, "conflicting reuse must be denied"
    except Denied as exc:
        assert str(exc) == "IDEMPOTENCY_CONFLICT"


def test_concurrent_reservations_never_exceed_budget():
    ledger = FakeLedger(Decimal("1.00"))

    def attempt(i):
        try:
            return ledger.reserve(f"r{i}", Decimal("0.20"))
        except Denied:
            return False

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(attempt, range(10)))

    assert sum(results) == 5
    assert ledger.reserved == Decimal("1.00")
    assert ledger.reserved <= ledger.budget


def test_unknown_final_cost_is_not_treated_as_zero():
    ledger = FakeLedger(Decimal("1.00"))
    ledger.reserve("timeout-1", Decimal("0.20"))
    ledger.mark_unknown("timeout-1")
    assert ledger.is_unknown("timeout-1")
    assert ledger.reserved == Decimal("0.20")


def test_invalid_token_estimate_fails_closed():
    guard, ledger, model = make_guard()
    for tokens in (-1, True, 1.5):
        try:
            guard.authorize("invalid-" + str(tokens), model, tokens, 10)
            assert False, "invalid input token estimate must be denied"
        except Denied as exc:
            assert str(exc) == "INVALID_TOKEN_ESTIMATE"
    assert ledger.reserved == 0