from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time
from app.language.semantic.semantic_intent import SemanticIntentEngine


def test_cold_semantic_index_does_not_block_rule_fallback(monkeypatch):
    import app.language.semantic.semantic_intent as module
    monkeypatch.setattr(module,'INTENT_PROTOTYPES',{'ask_general_info':['prototype']})
    release,started=Event(),Event()
    class Worker:
        def encode(self,text):
            if text=='prototype':
                started.set()
                assert release.wait(3)
            return {'ok':True,'embedding':[1.]*768}
    engine=SemanticIntentEngine(Worker())
    with ThreadPoolExecutor() as pool:
        result=pool.submit(engine.classify,'Pertanyaan pertama')
        try:
            response=result.result(timeout=.3)
            assert response['ok'] is False
            assert response['error']=='SEMANTIC_INDEX_WARMING'
        finally:
            release.set()
    deadline=time.monotonic()+2
    while not engine.health()['ready'] and time.monotonic()<deadline:
        time.sleep(.01)
    assert engine.classify('Pertanyaan berikutnya')['ok'] is True
