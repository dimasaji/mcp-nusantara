import sys
import time

from app.language.semantic.indobert_client import IndoBERTClient


def test_hung_worker_is_terminated_and_can_recover(tmp_path):
    worker = tmp_path / "worker.py"
    worker.write_text("import time\ntime.sleep(10)\n")
    client = IndoBERTClient(sys.executable, str(worker), response_timeout_s=.15)
    started = time.perf_counter()
    result = client.encode("hello")
    assert not result["ok"] and "timeout" in result["error"]
    assert time.perf_counter() - started < 3
    assert not client.is_running()
    worker.write_text("import sys,json\nfor line in sys.stdin:\n print(json.dumps({'ok':True,'embedding':[1,2]}),flush=True)\n")
    client.response_timeout_s = 3
    assert client.encode("hello")["ok"]
    client.stop()
    assert not client.is_running()
