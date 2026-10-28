"""Persistent, fail-closed SQLite ledger for V1 provider cost reservations."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path


class CostGovernanceDenied(RuntimeError):
    """Safe denial code only; do not attach credentials or request contents."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _decimal(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise CostGovernanceDenied("INVALID_AMOUNT") from None
    if not result.is_finite() or result <= 0:
        raise CostGovernanceDenied("INVALID_AMOUNT")
    return result


def _policy_cents(value) -> int:
    amount = _decimal(value)
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise CostGovernanceDenied("POLICY_MUST_USE_CENTS")
    return int(cents)


def _cost_cents(value) -> int:
    amount = _decimal(value)
    return int((amount * 100).to_integral_value(rounding=ROUND_CEILING))


def _actual_cents(value) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise CostGovernanceDenied("INVALID_ACTUAL_COST") from None
    if not amount.is_finite() or amount < 0:
        raise CostGovernanceDenied("INVALID_ACTUAL_COST")
    return int((amount * 100).to_integral_value(rounding=ROUND_CEILING))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CostLedger:
    """SQLite-backed reservations. Unknown outcomes remain budget-consuming."""

    def __init__(self, path: Path | str, *, budget_usd, per_request_cap_usd):
        self.path = Path(path)
        self.budget_cents = _policy_cents(budget_usd)
        self.cap_cents = _policy_cents(per_request_cap_usd)
        if self.cap_cents > self.budget_cents:
            raise CostGovernanceDenied("INVALID_POLICY")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS cost_policy (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    currency TEXT NOT NULL,
                    budget_cents INTEGER NOT NULL,
                    cap_cents INTEGER NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS cost_reservations (
                    request_id TEXT PRIMARY KEY,
                    reserved_cents INTEGER NOT NULL CHECK(reserved_cents > 0),
                    actual_cents INTEGER,
                    status TEXT NOT NULL CHECK(
                        status IN ('reserved', 'unknown', 'settled')
                    ),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            row = db.execute(
                "SELECT currency, budget_cents, cap_cents "
                "FROM cost_policy WHERE singleton = 1"
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO cost_policy "
                    "(singleton, currency, budget_cents, cap_cents) "
                    "VALUES (1, 'USD', ?, ?)",
                    (self.budget_cents, self.cap_cents),
                )
            elif row != ("USD", self.budget_cents, self.cap_cents):
                raise CostGovernanceDenied("POLICY_MISMATCH")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(str(self.path), timeout=10, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout = 10000")
            db.execute("PRAGMA foreign_keys = ON")
            yield db
        finally:
            db.close()

    def reserve(self, request_id: str, amount_usd) -> bool:
        if not isinstance(request_id, str) or not request_id.strip():
            raise CostGovernanceDenied("INVALID_REQUEST_ID")
        cents = _cost_cents(amount_usd)
        if cents > self.cap_cents:
            raise CostGovernanceDenied("REQUEST_CAP_EXCEEDED")

        with self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                existing = db.execute(
                    "SELECT reserved_cents FROM cost_reservations "
                    "WHERE request_id = ?", (request_id,)
                ).fetchone()
                if existing is not None:
                    if existing[0] != cents:
                        raise CostGovernanceDenied("IDEMPOTENCY_CONFLICT")
                    db.execute("COMMIT")
                    return False

                used = db.execute("""
                    SELECT COALESCE(SUM(
                        CASE WHEN status = 'settled'
                             THEN actual_cents
                             ELSE reserved_cents END
                    ), 0)
                    FROM cost_reservations
                """).fetchone()[0]

                if used + cents > self.budget_cents:
                    raise CostGovernanceDenied("BUDGET_EXCEEDED")

                now = _now()
                db.execute("""
                    INSERT INTO cost_reservations
                    (request_id, reserved_cents, actual_cents, status,
                     created_at, updated_at)
                    VALUES (?, ?, NULL, 'reserved', ?, ?)
                """, (request_id, cents, now, now))
                db.execute("COMMIT")
                return True
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise

    def mark_unknown(self, request_id: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute("""
                UPDATE cost_reservations
                SET status = 'unknown', updated_at = ?
                WHERE request_id = ? AND status IN ('reserved', 'unknown')
            """, (_now(), request_id))
            if cursor.rowcount != 1:
                db.execute("ROLLBACK")
                raise CostGovernanceDenied("RESERVATION_NOT_FOUND")
            db.execute("COMMIT")

    def settle(self, request_id: str, actual_cost_usd) -> None:
        actual = _actual_cents(actual_cost_usd)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""
                SELECT status, actual_cents
                FROM cost_reservations WHERE request_id = ?
            """, (request_id,)).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise CostGovernanceDenied("RESERVATION_NOT_FOUND")
            if row[0] == "settled":
                if row[1] != actual:
                    db.execute("ROLLBACK")
                    raise CostGovernanceDenied("SETTLEMENT_CONFLICT")
                db.execute("COMMIT")
                return
            db.execute("""
                UPDATE cost_reservations
                SET actual_cents = ?, status = 'settled', updated_at = ?
                WHERE request_id = ?
            """, (actual, _now(), request_id))
            db.execute("COMMIT")

    @property
    def reserved_usd(self) -> Decimal:
        with self._connect() as db:
            cents = db.execute("""
                SELECT COALESCE(SUM(
                    CASE WHEN status = 'settled'
                         THEN actual_cents
                         ELSE reserved_cents END
                ), 0)
                FROM cost_reservations
            """).fetchone()[0]
        return Decimal(cents) / Decimal(100)

    def status(self, request_id: str) -> str | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT status FROM cost_reservations WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return row[0] if row else None

    def summary(self) -> dict:
        """One read transaction; unknown outcomes consume their full reservation."""
        with self._connect() as db:
            db.execute('BEGIN')
            policy = db.execute('SELECT budget_cents, cap_cents FROM cost_policy WHERE singleton=1').fetchone()
            totals = db.execute("""SELECT
                COALESCE(SUM(CASE WHEN status='settled' THEN actual_cents ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN status!='settled' THEN reserved_cents ELSE 0 END),0),
                MIN(created_at), MAX(updated_at) FROM cost_reservations""").fetchone()
            db.row_factory = sqlite3.Row
            history = [dict(row) for row in db.execute(
                'SELECT request_id,reserved_cents,actual_cents,status,created_at,updated_at '
                'FROM cost_reservations ORDER BY created_at DESC,request_id LIMIT 100')]
            db.execute('COMMIT')
        money = lambda cents: format(Decimal(cents) / 100, '.2f')
        return {'status':'AVAILABLE','source':'CostLedger','currency':'USD',
                'period':{'scope':'LEDGER_LIFETIME','start':totals[2],'end':totals[3]},
                'actual_usd':money(totals[0]),'reserved_usd':money(totals[1]),
                'budget_usd':money(policy[0]),'per_request_cap_usd':money(policy[1]),
                'remaining_budget_usd':money(policy[0]-totals[0]-totals[1]),
                'estimated_usd':None,'provider_balance_usd':None,
                'input_tokens':None,'output_tokens':None,'provider':None,'model':None,
                'reason':'Token, model, provider, estimasi dan saldo provider tidak dicatat ledger ini.',
                'history':history,'checked_at':_now()}
