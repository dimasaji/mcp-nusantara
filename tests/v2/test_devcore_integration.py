"""Integrasi agent.py LIVE (integration/agent_with_devcore.py) dengan STUB dependensi & STUB ToolRegistry.
Membuktikan: run() tidak berubah, adapter menormalkan beberapa bentuk hasil registry, gerbang DevCore tetap
melindungi walau registry live tidak punya proteksi. TIDAK membuktikan kompatibilitas dengan registry.py asli."""
import asyncio
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path

from app.devcore import RegistryBackend, normalize_result

ROOT = Path(__file__).resolve().parents[2]
HEALTH = 'import urllib.request\nurllib.request.urlopen(\n    "http://127.0.0.1:8000/health",\n    timeout=3\n)\n'


class Obj:  # objek ala pydantic ToolResult
    def __init__(self, **kw): self.__dict__.update(kw)
    def model_dump(self): return dict(self.__dict__)


def stub_modules(registry_cls):
    def mod(name, **attrs):
        m = types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name] = m

    class Mock:
        async def generate(self, req): return {"content": "Tidak ada print(). Request HTTP ke localhost timeout 3 detik. Tidak ada retry."}

    class Router:
        def register(self, p): return self

    class Eng:
        def __init__(self, *a, **k): pass
        def process(self, *a, **k): return {"lang": "id"}
        def analyze(self, **k): return {"goal": "g"}

    mod("app.models.mock", MockProvider=Mock); mod("app.models.router", ModelRouter=Router)
    mod("app.language.engine", LanguageEngine=Eng)
    mod("app.problem.engine", ProblemEngine=Eng); mod("app.problem.detector", ProblemDetector=Eng)
    mod("app.problem.classifier", ProblemClassifier=Eng); mod("app.reasoning.engine", ReasoningEngine=Eng)
    mod("app.tools.registry", ToolRegistry=registry_cls)


def load_agent(src: Path, root: Path, registry_cls):
    stub_modules(registry_cls)
    dest = root / "app" / "hermes"; dest.mkdir(parents=True, exist_ok=True)
    (dest / "agent.py").write_text(src.read_text())
    spec = importlib.util.spec_from_file_location(f"agent_{src.stem}", dest / "agent.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.HermesAgent()


class NaiveRegistry:
    """Registry palsu TANPA proteksi path (worst case) dengan hasil dibungkus {success, tool_name, result}."""
    def __init__(self, workspace): self.root = Path(workspace); self.calls = []
    def list_tools(self): return ["read_file", "find_file", "list_directory"]
    def execute(self, name, args):
        self.calls.append((name, args))
        if name == "read_file":
            p = self.root / args["path"]
            if not p.is_file(): raise FileNotFoundError(args["path"])
            return Obj(success=True, tool_name=name, result={"success": True, "path": str(p), "content": p.read_text()})
        if name == "find_file":
            return Obj(success=True, tool_name=name, result={"matches": [str(x) for x in self.root.rglob(args["name"])]})
        if name == "list_directory":
            return Obj(success=True, tool_name=name, result=[x.name + ("/" if x.is_dir() else "") for x in (self.root / args.get("path", ".")).iterdir()])
        raise KeyError(name)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.r = Path(self.d.name)
        for rel, txt in {"scripts/healthcheck.py": HEALTH, "app/main.py": "x = 1\n", ".env": "SECRET=abc\n",
                         "app/tools/registry.py": "class ToolRegistry: pass\n"}.items():
            (self.r / rel).parent.mkdir(parents=True, exist_ok=True); (self.r / rel).write_text(txt)
        self.addCleanup(self.d.cleanup)

    def test_run_unchanged(self):
        orig = load_agent(ROOT / "integration" / "agent_live_original.py", self.r, NaiveRegistry)
        new = load_agent(ROOT / "integration" / "agent_with_devcore.py", self.r, NaiveRegistry)
        self.assertEqual(orig.run("halo", "s1"), new.run("halo", "s1"))
        self.assertEqual(orig.list_tools(), new.list_tools())
        self.assertFalse(new.is_dev_request("halo apa kabar")); self.assertTrue(new.is_dev_request("Baca app/main.py"))

    def test_run_dev_contract16(self):
        a = load_agent(ROOT / "integration" / "agent_with_devcore.py", self.r, NaiveRegistry)
        out = asyncio.run(a.run_dev("Baca scripts/healthcheck.py. Tampilkan isi file tersebut persis lalu jelaskan"))
        self.assertTrue(out["tool"]["used"]); self.assertEqual(out["tool"]["name"], "read_file")
        self.assertTrue(out["tool"]["result"]["success"])
        self.assertEqual(out["tool"]["result"]["path"], "scripts/healthcheck.py")  # path absolut dinormalkan ke relatif
        self.assertEqual(out["tool"]["result"]["content"], HEALTH)
        self.assertEqual(out["verification"]["status"], "passed")
        self.assertEqual(a.run_dev_sync("Baca app/main.py")["tool"]["result"]["content"], "x = 1\n")

    def test_sync_inside_running_loop(self):
        a = load_agent(ROOT / "integration" / "agent_with_devcore.py", self.r, NaiveRegistry)
        async def inner(): return a.run_dev_sync("Baca app/main.py")
        self.assertTrue(asyncio.run(inner())["tool"]["result"]["success"])

    def test_gate_protects_even_if_registry_is_naive(self):
        a = load_agent(ROOT / "integration" / "agent_with_devcore.py", self.r, NaiveRegistry)
        for bad in ("Baca .env", "Baca ../../etc/passwd.txt", "Baca /etc/hosts.txt"):
            o = asyncio.run(a.run_dev(bad))
            self.assertFalse(o["tool"]["result"]["success"], bad); self.assertNotIn("SECRET=abc", o["answer"])
        self.assertEqual([c for c in a.tools.calls if c[0] == "read_file"], [])  # registry TIDAK dipanggil untuk path terlarang
        o = asyncio.run(a.run_dev("Tampilkan isi folder ."))
        self.assertNotIn(".env", o["answer"])  # daftar dari registry difilter
        o = asyncio.run(a.run_dev("Cari file registry.py"))
        self.assertIn("app/tools/registry.py", o["answer"])

    def test_normalize_shapes(self):
        n = normalize_result
        self.assertEqual(n("read_file", {"success": True, "path": "a", "content": "x"})["content"], "x")
        self.assertEqual(n("read_file", Obj(success=True, tool_name="read_file", result="isi"))["content"], "isi")
        r = n("read_file", {"success": True, "result": {"success": False, "error": "nf"}})
        self.assertFalse(r["success"]); self.assertEqual(r["error"], "nf")
        self.assertEqual(n("find_file", {"success": True, "result": ["a/b.py"]})["matches"], ["a/b.py"])
        self.assertEqual(n("list_directory", {"success": True, "result": ["d/", "f.py"]})["entries"][0], {"name": "d", "type": "dir"})
        self.assertFalse(n("read_file", {"success": False, "error": "boom"})["success"])

    def test_registry_errors_and_arg_mapping(self):
        class R:
            def execute(self, name, args): raise RuntimeError("kaboom " + ",".join(sorted(args)))
        b = RegistryBackend(R(), arg_names={"find_file": {"name": "query"}})
        r = b.execute("find_file", {"name": "x"})
        self.assertFalse(r["success"]); self.assertIn("query", r["error"])


if __name__ == "__main__":
    unittest.main()
