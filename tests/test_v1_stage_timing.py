"""Observe the actual V1 stage runner without starting live providers."""
import ast
import asyncio
import threading
import time
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.observability import metrics


def stage_runner():
    tree = ast.parse(Path('app/api/routes.py').read_text(encoding='utf-8-sig'))
    node = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == '_run_sync_v1')
    namespace = {'asyncio': asyncio, 'time': time, 'HTTPException': HTTPException,
                 '_sync_slots': threading.BoundedSemaphore(1)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'v1-stage-runner', 'exec'), namespace)
    return namespace['_run_sync_v1']


@pytest.mark.parametrize('fail', [False, True])
def test_stage_runner_records_success_and_failure_duration(fail):
    def audit_fixture_stage():
        if fail:
            raise ValueError('fixture failure')
        return 'completed'

    name = 'v1.stage.audit_fixture_stage'
    before = metrics.snapshot()['latency'].get(name, {}).get('count', 0)
    execute = stage_runner()
    if fail:
        with pytest.raises(ValueError, match='fixture failure'):
            asyncio.run(execute(audit_fixture_stage))
    else:
        assert asyncio.run(execute(audit_fixture_stage)) == 'completed'
    assert metrics.snapshot()['latency'][name]['count'] == before + 1


@pytest.mark.parametrize('mode', ['ok', 'error', 'timeout', 'busy'])
def test_metrics_failure_never_replaces_stage_result_or_error(monkeypatch, mode):
    def broken_metrics(*args, **kwargs):
        raise RuntimeError('metrics unavailable')

    monkeypatch.setattr(metrics, 'observe', broken_metrics)
    monkeypatch.setattr(metrics, 'incr', broken_metrics)
    execute = stage_runner()

    def read_stage():
        if mode == 'error':
            raise ValueError('original failure')
        if mode == 'timeout':
            time.sleep(.02)
        return 'completed'

    if mode == 'ok':
        assert asyncio.run(execute(read_stage)) == 'completed'
    elif mode == 'error':
        with pytest.raises(ValueError, match='original failure'):
            asyncio.run(execute(read_stage))
    else:
        if mode == 'busy':
            execute.__globals__['_sync_slots'].acquire()
        with pytest.raises(HTTPException) as failure:
            asyncio.run(execute(read_stage, timeout_s=.001))
        assert failure.value.status_code == (503 if mode == 'busy' else 504)
