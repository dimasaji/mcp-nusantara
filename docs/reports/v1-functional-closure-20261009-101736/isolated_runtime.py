"""Controlled test composition: actual V1/Hermes with explicit external fixtures."""
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LOCAL_PROVIDER = os.getenv('V1_LOCAL_PROVIDER') == '1'
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['NUSANTARA_ADMIN_TOKEN'] = 'isolated-operator-fixture'
os.environ['NUSANTARA_DATA_DIR'] = str(OUT / 'runtime-data')
if __name__ == '__main__':
    import builtins, io, socket, sqlite3, subprocess
    def blocked(*args, **kwargs):
        raise AssertionError('CANDIDATE_EXTERNAL_EFFECT_BLOCKED')
    sqlite3.connect = blocked
    subprocess.Popen.__init__ = blocked
    os.system = blocked
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    def socketpair_only(self, address):
        frame = sys._getframe(1)
        listener = frame.f_locals.get('lsock')
        if (frame.f_code is socket._fallback_socketpair.__code__ and listener is not None
                and address == listener.getsockname()):
            return connect(self, address)
        if LOCAL_PROVIDER and isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1') and address[1] == 11434:
            return connect(self, address)
        return blocked()
    socket.socket.connect = socketpair_only
    def local_connect_ex(self, address):
        if LOCAL_PROVIDER and isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1') and address[1] == 11434:
            return connect_ex(self, address)
        return blocked()
    socket.socket.connect_ex = local_connect_ex
    def opened(original):
        def guarded(file, mode='r', *args, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)):
                path = Path(os.fsdecode(file)).resolve()
                if path.is_relative_to(ROOT / 'data'):
                    blocked()
                if any(c in str(mode) for c in 'wax+') and not path.is_relative_to(OUT):
                    blocked()
            return original(file, mode, *args, **kwargs)
        return guarded
    builtins.open = opened(builtins.open)
    io.open = opened(io.open)
from app.core.config import Settings
import app.core.config as config_module
if LOCAL_PROVIDER:
    owner = config_module.settings
    # Same existing owner; only this controlled candidate uses NORMAL single-worker bootstrap.
    owner.compose_configuration(overrides={'runtime': {'profile': 'NORMAL', 'workers': 1}})
    from urllib.parse import urlsplit
    address = urlsplit(owner.effective_configuration.llm.base_url)
    if address.hostname not in ('localhost', '127.0.0.1', '::1') or address.port != 11434:
        raise RuntimeError('EXPLICIT_LOCAL_OLLAMA_ONLY')
else:
    owner = Settings(_env_file=None)
    owner.compose_configuration(project_root=OUT / 'runtime-data', environment={}, dotenv_environment={},
                                overrides={'llm': {'model': 'fixture-a', 'base_url': 'http://127.0.0.1:1'}})
config_module.settings = owner

class FixtureLanguage:
    semantic_intent_engine = None
    def process(self, text):
        return {'output': {'intent': {'intent': 'ask_general_info', 'confidence': .95}, 'entities': []}}

language = ModuleType('app.language.engine')
language.LanguageEngine = FixtureLanguage
sys.modules['app.language.engine'] = language
from fastapi import APIRouter
v2 = ModuleType('app.api.v2_routes')
v2.router = APIRouter()
sys.modules['app.api.v2_routes'] = v2  # V2 is not exercised or modified by this fixture

from app.knowledge.schemas import Evidence
TEXT = 'KTP-el adalah dokumen identitas penduduk.'
class FixtureRetrieval:
    _embedding_adapter = SimpleNamespace(client=None)
    def query(self, **kwargs):
        evidence = Evidence(document_id='FIXTURE-NOT-OFFICIAL', title='Isolated fixture',
                            source='fixture://not-official', chunk=TEXT, score=.9,
                            chunk_id='fixture-1', chunk_index=0, start_char=0, end_char=len(TEXT))
        return SimpleNamespace(evidence_pack=SimpleNamespace(evidence=[evidence]), effective_profile=None)

import app.knowledge.rag as rag
original_create = rag.create_rag
rag.create_rag = lambda **kwargs: FixtureRetrieval()
import app.knowledge.engine as knowledge
from app.main import app
rag.create_rag = knowledge.create_rag = original_create

import httpx
from app.models.ollama import OllamaProvider
observed = []
def transport(request):
    if request.url.path == '/api/tags':
        return httpx.Response(200, json={'models': [{'name': 'fixture-a'}, {'name': 'fixture-b'}]})
    if request.url.path == '/api/generate':
        payload = json.loads(request.content)
        observed.append(payload['model'])
        return httpx.Response(200, json={'model': payload['model'], 'response': TEXT, 'done': True})
    raise AssertionError('UNEXPECTED_PROVIDER_OPERATION')

original_client = OllamaProvider._get_client
async def fixture_client(self):
    if self._client is None or self._client.is_closed:
        self._client = httpx.AsyncClient(base_url=self.base_url, transport=httpx.MockTransport(transport))
    return self._client
if not LOCAL_PROVIDER:
    OllamaProvider._get_client = fixture_client
else:
    original_emit = OllamaProvider._emit_identity
    def observe_local_identity(self, receipt, *, failed=False):
        original_emit(receipt, failed=failed)
        with (OUT / 'LOCAL_PROVIDER_RECEIPTS.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'failed': failed, **receipt.safe_dump()}) + '\n')
    OllamaProvider._emit_identity = observe_local_identity

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=18011, log_config=None, access_log=False)

