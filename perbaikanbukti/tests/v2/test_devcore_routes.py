"""Uji routes.py LIVE (patched vs original) dengan STUB fastapi/pydantic/Ollama/registry.
Membuktikan: routing generik menggantikan hard-code, kontrak respons /v1/chat tetap, jalur non-dev identik,
Ollama offline tidak crash. TIDAK membuktikan kompatibilitas dengan registry.py / Ollama / FastAPI asli."""
import asyncio
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path

from tests.v2.test_devcore_integration import HEALTH, NaiveRegistry, stub_modules

ROOT = Path(__file__).resolve().parents[2]
GOOD = "Tidak ada print(). Request HTTP ke localhost timeout 3 detik. Tidak ada retry."


def mod(name, **attrs):
    m = types.ModuleType(name); m.__dict__.update(attrs); m.__path__ = []; sys.modules[name] = m
    return m


class FakeProvider:
    available = True
    prompts: list = []

    def __init__(self, base_url=None, model=None): self.model = model or "stub-model"
    async def health_check(self): return {"available": FakeProvider.available}
    async def generate(self, req):
        FakeProvider.prompts.append(req["prompt"])
        return {"content": GOOD, "model": self.model, "latency_ms": 5}
    async def close(self): pass


class StubModel:
    def __init__(self, **kw):
        for k, v in kw.items(): setattr(self, k, v)


def load_routes(routes_src: Path, agent_src: Path, root: Path):
    stub_modules(NaiveRegistry)  # registry + engine stub untuk agent.py
    mod("fastapi", APIRouter=lambda **k: types.SimpleNamespace(
        get=lambda *a, **kw: (lambda f: f), post=lambda *a, **kw: (lambda f: f), delete=lambda *a, **kw: (lambda f: f)),
        HTTPException=type("HTTPException", (Exception,), {"__init__": lambda s, status_code, detail: (setattr(s, "status_code", status_code), setattr(s, "detail", detail), None)[-1]}),
        Request=object)
    mod("pydantic", BaseModel=StubModel, Field=lambda default=None, **k: None if default is Ellipsis else (k.get("default_factory") or (lambda: default))() if "default_factory" in k else (None if default is Ellipsis else default))
    mod("app.core.config", settings=types.SimpleNamespace(app_version="t", app_name="n", llm_base_url="x", llm_model="m", retrieval_top_k=3))
    mod("app.knowledge"); mod("app.knowledge.engine", KnowledgeEngine=lambda: types.SimpleNamespace(search_knowledge=lambda q, top_k=3: []))
    mod("app.knowledge.schemas", DocumentIngestRequest=StubModel)
    mod("app.models.ollama", OllamaProvider=FakeProvider)
    mod("app.workflow"); mod("app.workflow.engine", WorkflowEngine=lambda: object())
    d = root / "app" / "hermes"; d.mkdir(parents=True, exist_ok=True)
    (d / "agent.py").write_text(agent_src.read_text())
    sp = importlib.util.spec_from_file_location("app.hermes.agent", d / "agent.py")
    am = importlib.util.module_from_spec(sp); sys.modules["app.hermes.agent"] = am; sp.loader.exec_module(am)
    mod("app.hermes"); sys.modules["app.hermes"].agent = am
    (root / "app" / "api").mkdir(parents=True, exist_ok=True)
    (root / "app" / "api" / "routes.py").write_text(routes_src.read_text())
    sp = importlib.util.spec_from_file_location("routes_under_test", root / "app" / "api" / "routes.py")
    rm = importlib.util.module_from_spec(sp); sp.loader.exec_module(rm)
    return rm


class TestRoutes(unittest.TestCase):
    def setUp(self):
        saved = dict(sys.modules)
        def restore():
            for k in list(sys.modules):
                if k not in saved: del sys.modules[k]
            sys.modules.update(saved)
        self.addCleanup(restore)
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        self.r = Path(self.d.name)
        for rel, txt in {"scripts/healthcheck.py": HEALTH, "app/main.py": "x = 1\n", "app/api/routes_stub.py": "y = 2\n",
                         "app/tools/registry.py": "class ToolRegistry: pass\n", ".env": "SECRET=abc\n"}.items():
            (self.r / rel).parent.mkdir(parents=True, exist_ok=True); (self.r / rel).write_text(txt)
        FakeProvider.available = True; FakeProvider.prompts = []
        self.new = load_routes(ROOT / "integration/routes_with_devcore.py", ROOT / "integration/agent_with_devcore.py", self.r)
        self.chat = lambda text, **kw: asyncio.run(self.new.chat(self.new.ChatRequest(user_input=text, **kw)))

    def test_contract16_and_response_shape(self):
        o = self.chat("Baca scripts/healthcheck.py. Tampilkan isi file tersebut persis lalu jelaskan apa yang benar-benar dilakukan script.")
        self.assertTrue({"session_id", "response", "model", "provider_status", "latency_ms", "understanding", "problem", "tool",
                         "available_tools", "evidence", "timestamp", "developer"} <= set(o))
        self.assertEqual((o["tool"]["used"], o["tool"]["name"], o["tool"]["result"]["success"]), (True, "read_file", True))
        self.assertEqual(o["tool"]["result"]["content"], HEALTH)
        self.assertIn(HEALTH, o["response"])
        self.assertEqual(o["developer"]["verification"]["status"], "passed")
        self.assertEqual(o["provider_status"], "ollama"); self.assertEqual(len(FakeProvider.prompts), 1)  # satu panggilan LLM

    def test_generic_not_hardcoded(self):
        for text, path in (("Baca healthcheck.py", "scripts/healthcheck.py"), ("Baca app/main.py", "app/main.py"),
                           ("Analisis app\\main.py", "app/main.py"), ("Cek app/tools/registry.py", "app/tools/registry.py")):
            o = self.chat(text)
            self.assertEqual((o["tool"]["name"], o["tool"]["result"]["path"]), ("read_file", path), text)

    def test_non_dev_path_identical_to_original(self):
        # routes ASLI dijalankan di atas agent yang sudah dipatch (agent lama tidak punya is_dev_request, tapi routes asli tidak memanggilnya)
        old = load_routes(ROOT / "integration/routes_live_original.py", ROOT / "integration/agent_with_devcore.py", self.r)
        run = lambda m: asyncio.run(m.chat(m.ChatRequest(user_input="halo, apa kabar?", session_id="s1")))
        a, b = run(old), run(self.new)
        for k in ("timestamp",): a.pop(k); b.pop(k)
        self.assertIsNone(b.pop("developer")); self.assertEqual(a, b)
        self.assertEqual(b["tool"], {"used": False, "name": None, "result": None})
        self.assertIn("INPUT PENGGUNA", FakeProvider.prompts[0])  # prompt lama tetap dipakai

    def test_old_route_only_handled_healthcheck(self):  # bukti regresi diperbaiki
        old = load_routes(ROOT / "integration/routes_live_original.py", ROOT / "integration/agent_with_devcore.py", self.r)
        o = asyncio.run(old.chat(old.ChatRequest(user_input="Baca app/main.py")))
        self.assertFalse(o["tool"]["used"])  # perilaku lama: file lain tidak dibaca
        self.assertTrue(self.chat("Baca app/main.py")["tool"]["used"])

    def test_ollama_offline_uses_static_facts(self):
        FakeProvider.available = False
        o = self.chat("Baca scripts/healthcheck.py")
        self.assertEqual(o["provider_status"], "offline"); self.assertEqual(FakeProvider.prompts, [])
        self.assertIn("timeout=3", o["response"]); self.assertEqual(o["developer"]["verification"]["status"], "fallback_static_facts")

    def test_blocked_and_modify(self):
        o = self.chat("Baca .env")
        self.assertFalse(o["tool"]["result"]["success"]); self.assertNotIn("SECRET=abc", str(o))
        self.assertEqual(FakeProvider.prompts, [])
        before = (self.r / "app/main.py").read_text()
        o = self.chat("Ubah app/main.py dan hapus isinya")
        self.assertTrue(o["developer"]["modify_blocked"]); self.assertEqual((self.r / "app/main.py").read_text(), before)


if __name__ == "__main__":
    unittest.main()
