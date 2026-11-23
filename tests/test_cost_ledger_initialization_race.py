"""Synthetic fault-injection regression for concurrent cost policy initialization.

The competing writer is simulated inside the SQLite seam; it is not a real
second process. It proves that a policy row appearing between the first policy
statement and policy validation does not break ledger construction.
"""
import sqlite3
from types import SimpleNamespace

from app.models.cost_ledger import CostLedger


def test_initialization_tolerates_competing_policy_writer(monkeypatch, tmp_path):
    path = tmp_path / 'ledger.db'
    real_connect = sqlite3.connect
    observed = {'injected': 0}

    class RacingConnection:
        def __init__(self, connection):
            self._connection = connection
            self._policy_seen = False

        def execute(self, sql, params=()):
            cursor = self._connection.execute(sql, params)
            if 'cost_policy' in sql and 'CREATE TABLE' not in sql.upper():
                if not self._policy_seen:
                    self._policy_seen = True
                    competitor = real_connect(str(path), isolation_level=None)
                    try:
                        competitor.execute(
                            "INSERT OR IGNORE INTO cost_policy "
                            "(singleton, currency, budget_cents, cap_cents) "
                            "VALUES (1, 'USD', ?, ?)",
                            (500, 100),
                        )
                        observed['injected'] += 1
                    finally:
                        competitor.close()
            return cursor

        def __getattr__(self, name):
            return getattr(self._connection, name)

    monkeypatch.setattr(
        'app.models.cost_ledger.sqlite3',
        SimpleNamespace(connect=lambda *a, **k: RacingConnection(real_connect(*a, **k))),
    )

    ledger = CostLedger(path, budget_usd='5', per_request_cap_usd='1')

    assert observed['injected'] == 1
    assert ledger.budget_cents == 500
    assert ledger.cap_cents == 100
