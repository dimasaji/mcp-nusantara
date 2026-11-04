"""Explicit V1 fixture, retaining exact source pins and immutable historical reports."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/v1-current-contract'
def current_contract():
    fixture=json.loads((FIXTURE/'source-contract.json').read_text(encoding='utf-8'))
    assert fixture['schema_version']==1 and fixture['authorization']
    for relative,expected in fixture['historical_reports'].items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected,relative
    return fixture

def assert_current_source(relative):
    fixture=current_contract()
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==fixture['current_sources'][relative],relative
