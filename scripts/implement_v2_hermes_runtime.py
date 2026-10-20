from __future__ import annotations

import ast
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HERMES = ROOT / "app" / "hermes" / "agent.py"
ORCH = ROOT / "app" / "v2" / "orchestrator.py"
ROUTES = ROOT / "app" / "api" / "v2_routes.py"

ADAPTER = ROOT / "app" / "v2" / "hermes_adapter.py"
TEST = ROOT / "tests" / "test_v2_hermes_runtime.py"

BACKUP_DIR = (
    ROOT
    / "data"
    / "developer_core"
    / "v2_hermes_patch_backups"
)

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[WRITE] {path}")


def backup(path: Path) -> None:
    if not path.exists():
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    destination = BACKUP_DIR / f"{path.name}.{TIMESTAMP}.bak"

    shutil.copy2(path, destination)

    print(f"[BACKUP] {path}")
    print(f"         -> {destination}")


def parse(path: Path) -> ast.AST:
    return ast.parse(read(path), filename=str(path))


def validate_python(path: Path) -> None:
    parse(path)
    print(f"[AST PASS] {path}")


def find_class(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def find_function(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    return None


def patch_hermes_agent() -> None:
    source = read(HERMES)
    tree = parse(HERMES)

    cls = find_class(tree, "HermesAgent")

    if cls is None:
        raise RuntimeError(
            "HermesAgent class tidak ditemukan. "
            "Patch dihentikan."
        )

    run_method = None

    for node in cls.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ) and node.name == "run":
            run_method = node
            break

    if run_method is None:
        raise RuntimeError(
            "HermesAgent.run() tidak ditemukan. "
            "Patch dihentikan."
        )

    # Pastikan source memang memakai reasoning.process.
    segment = ast.get_source_segment(source, run_method) or ""

    if "reasoning.process" not in segment:
        raise RuntimeError(
            "HermesAgent.run() tidak memanggil reasoning.process(). "
            "Patch dihentikan agar tidak mengubah arsitektur secara spekulatif."
        )

    # Jangan patch dua kali.
    if "knowledge_evidence = []" in segment:
        print(
            "[INFO] HermesAgent sudah memiliki knowledge_evidence boundary."
        )
        return

    lines = source.splitlines(keepends=True)

    # Cari pemanggilan reasoning.process().
    reasoning_call = None

    for node in ast.walk(run_method):
        if isinstance(node, ast.Call):
            func = node.func

            if (
                isinstance(func, ast.Attribute)
                and func.attr == "process"
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "reasoning"
            ):
                reasoning_call = node
                break

    if reasoning_call is None:
        raise RuntimeError(
            "Call reasoning.process() tidak dapat ditemukan. "
            "Patch dihentikan."
        )

    insert_line = reasoning_call.lineno - 1

    indentation = " " * (reasoning_call.col_offset)

    insertion = (
        f"{indentation}knowledge_evidence = []\n"
        f"{indentation}if isinstance(context, dict):\n"
        f"{indentation}    candidate_evidence = context.get("
        f"\"knowledge_evidence\", [])\n"
        f"{indentation}    if isinstance(candidate_evidence, list):\n"
        f"{indentation}        knowledge_evidence = candidate_evidence\n"
        f"\n"
    )

    lines.insert(insert_line, insertion)

    patched = "".join(lines)

    # Replace only the keyword argument if it is literally [].
    tree_after = ast.parse(patched, filename=str(HERMES))

    replaced = False

    for node in ast.walk(tree_after):
        if isinstance(node, ast.Call):
            func = node.func

            if (
                isinstance(func, ast.Attribute)
                and func.attr == "process"
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "reasoning"
            ):
                for keyword in node.keywords:
                    if keyword.arg == "knowledge_evidence":
                        if (
                            isinstance(keyword.value, ast.List)
                            and len(keyword.value.elts) == 0
                        ):
                            start = keyword.value.lineno - 1
                            end = keyword.value.end_lineno

                            original_lines = patched.splitlines(
                                keepends=True
                            )

                            replacement_indent = (
                                " " * keyword.value.col_offset
                            )

                            original_lines[start:end] = [
                                "knowledge_evidence"
                            ]

                            patched = "".join(original_lines)
                            replaced = True
                        break

    # Jika AST replacement di atas tidak menemukan [] karena formatting,
    # gunakan source segment lokal sebagai fallback aman.
    if not replaced:
        source_segment = ast.get_source_segment(
            patched,
            reasoning_call,
        ) or ""

        if "knowledge_evidence=[]" in source_segment:
            patched = patched.replace(
                "knowledge_evidence=[]",
                "knowledge_evidence=knowledge_evidence",
                1,
            )
            replaced = True
        elif "knowledge_evidence = []" in source_segment:
            patched = patched.replace(
                "knowledge_evidence = []",
                "knowledge_evidence=knowledge_evidence",
                1,
            )
            replaced = True

    if not replaced:
        # Coba pola umum tanpa mengubah bagian lain.
        candidates = [
            "knowledge_evidence=[]",
            "knowledge_evidence = []",
        ]

        for candidate in candidates:
            if candidate in patched:
                patched = patched.replace(
                    candidate,
                    "knowledge_evidence=knowledge_evidence",
                    1,
                )
                replaced = True
                break

    if not replaced:
        raise RuntimeError(
            "knowledge_evidence=[] tidak ditemukan sebagai argument "
            "reasoning.process(). Tidak melakukan perubahan."
        )

    ast.parse(patched, filename=str(HERMES))

    backup(HERMES)
    write(HERMES, patched)


def create_adapter() -> None:
    content = '''from __future__ import annotations

"""
Nusantara V2 -> Hermes runtime boundary.

Tidak membuat engine baru.
Menggunakan HermesAgent yang sudah ada.
"""

from typing import Any

from app.hermes.agent import HermesAgent


class HermesV2Adapter:
    VERSION = "1.0.0-v2-runtime"

    def __init__(
        self,
        agent: HermesAgent | None = None,
    ):
        self.agent = agent or HermesAgent()

    def run(
        self,
        *,
        user_input: str,
        session_id: str = "default",
        evidence: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        runtime_context = dict(context or {})

        runtime_context["knowledge_evidence"] = list(
            evidence or []
        )

        result = self.agent.run(
            user_input=user_input,
            session_id=session_id,
            context=runtime_context,
        )

        return {
            "engine": "hermes",
            "adapter_version": self.VERSION,
            "session_id": session_id,
            "understanding": result.get("understanding"),
            "problem": result.get("problem"),
            "reasoning": result.get("reasoning"),
        }
'''

    if ADAPTER.exists():
        existing = read(ADAPTER)

        if "class HermesV2Adapter" in existing:
            print("[INFO] HermesV2Adapter already exists.")
            return

        backup(ADAPTER)

    write(ADAPTER, content)


def patch_v2_orchestrator() -> None:
    source = read(ORCH)

    if "hermes:" in source and "self.hermes" in source:
        print("[INFO] V2Orchestrator Hermes boundary already exists.")
        return

    tree = parse(ORCH)

    cls = find_class(tree, "V2Orchestrator")

    if cls is None:
        raise RuntimeError(
            "V2Orchestrator tidak ditemukan."
        )

    init_method = None

    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            init_method = node
            break

    handle_method = None

    for node in cls.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "handle":
            handle_method = node
            break

    if init_method is None or handle_method is None:
        raise RuntimeError(
            "Constructor atau handle() V2Orchestrator tidak ditemukan."
        )

    lines = source.splitlines(keepends=True)

    # Tambahkan parameter hermes ke __init__ sebelum policy_check.
    init_line = init_method.lineno - 1
    init_segment = ast.get_source_segment(source, init_method) or ""

    if "hermes:" not in init_segment:
        target = "retrieve:"
        found = False

        for i in range(init_line, min(len(lines), init_method.end_lineno)):
            if target in lines[i]:
                indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]

                lines.insert(
                    i + 1,
                    f"{indent}hermes: Callable[..., Any] | None = None,\n",
                )

                found = True
                break

        if not found:
            raise RuntimeError(
                "Parameter retrieve pada V2Orchestrator tidak ditemukan."
            )

    patched = "".join(lines)

    tree = ast.parse(patched, filename=str(ORCH))

    cls = find_class(tree, "V2Orchestrator")

    init_method = None

    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            init_method = node
            break

    # Tambahkan self.hermes setelah self.retrieve.
    lines = patched.splitlines(keepends=True)

    inserted = False

    for i in range(
        init_method.lineno - 1,
        init_method.end_lineno,
    ):
        if "self.generate" in lines[i] and "self.retrieve" in lines[i]:
            indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]

            lines.insert(
                i + 1,
                f"{indent}self.hermes = hermes\n",
            )

            inserted = True
            break

    if not inserted:
        raise RuntimeError(
            "Assignment self.generate/self.retrieve tidak ditemukan."
        )

    patched = "".join(lines)

    tree = ast.parse(patched, filename=str(ORCH))

    cls = find_class(tree, "V2Orchestrator")

    handle_method = None

    for node in cls.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "handle":
            handle_method = node
            break

    # Cari pemanggilan retrieve dan sisipkan Hermes setelahnya.
    lines = patched.splitlines(keepends=True)

    inserted = False

    for i in range(
        handle_method.lineno - 1,
        handle_method.end_lineno,
    ):
        if (
            "evidence = await self._stage" in lines[i]
            and "retrieve" in lines[i]
        ):
            # Cari akhir blok evidence = evidence or []
            for j in range(i, min(i + 20, len(lines))):
                if "evidence = evidence or []" in lines[j]:
                    indent = lines[j][: len(lines[j]) - len(lines[j].lstrip())]

                    block = [
                        "\n",
                        f"{indent}hermes_result = None\n",
                        f"{indent}if self.hermes is not None:\n",
                        f"{indent}    hermes_result = await self._stage(\n",
                        f"{indent}        res,\n",
                        f'{indent}        "hermes",\n',
                        f"{indent}        self.hermes,\n",
                        f"{indent}        text,\n",
                        f"{indent}        session_id,\n",
                        f"{indent}        evidence,\n",
                        f'{indent}        breaker="understand",\n',
                        f"{indent}    )\n",
                        "\n",
                    ]

                    lines[j + 1:j + 1] = block
                    inserted = True
                    break

        if inserted:
            break

    if not inserted:
        raise RuntimeError(
            "Boundary retrieve pada V2Orchestrator tidak ditemukan."
        )

    patched = "".join(lines)

    ast.parse(patched, filename=str(ORCH))

    backup(ORCH)
    write(ORCH, patched)


def patch_v2_routes() -> None:
    source = read(ROUTES)

    if "HermesV2Adapter" in source and "hermes_core" in source:
        print("[INFO] /v2/chat Hermes wiring sudah ada.")
        return

    if "from app.v2.orchestrator import V2Orchestrator" not in source:
        raise RuntimeError(
            "Import V2Orchestrator tidak ditemukan di v2_routes.py."
        )

    source = source.replace(
        "from app.v2.orchestrator import V2Orchestrator",
        (
            "from app.v2.orchestrator import V2Orchestrator\n"
            "from app.v2.hermes_adapter import HermesV2Adapter"
        ),
        1,
    )

    if "orch = V2Orchestrator(" not in source:
        raise RuntimeError(
            "Instansiasi V2Orchestrator tidak ditemukan."
        )

    marker = "    orch = V2Orchestrator("

    position = source.find(marker)

    adapter_block = (
        '    hermes = HermesV2Adapter()\n'
        "\n"
        "    async def hermes_core(text, session_id, evidence):\n"
        "        return hermes.run(\n"
        "            user_input=text,\n"
        "            session_id=session_id,\n"
        "            evidence=evidence,\n"
        "        )\n"
        "\n"
    )

    source = source[:position] + adapter_block + source[position:]

    # Tambahkan hermes=hermes_core jika belum ada.
    orch_position = source.find(marker)

    close_position = source.find(
        "    )",
        orch_position,
    )

    if close_position == -1:
        raise RuntimeError(
            "Penutup V2Orchestrator tidak ditemukan."
        )

    before_close = source[:close_position]

    if "hermes=hermes_core" not in before_close:
        before_close += "                          hermes=hermes_core,\n"

    source = before_close + source[close_position:]

    ast.parse(source, filename=str(ROUTES))

    backup(ROUTES)
    write(ROUTES, source)


def create_test() -> None:
    content = '''from __future__ import annotations

from app.v2.hermes_adapter import HermesV2Adapter


class FakeHermes:

    def __init__(self):
        self.received_context = None

    def run(
        self,
        user_input,
        session_id="default",
        context=None,
    ):
        self.received_context = context

        return {
            "session_id": session_id,
            "understanding": {
                "text": user_input
            },
            "problem": {
                "goal": "test"
            },
            "reasoning": {
                "answer": "test reasoning"
            },
        }


def test_hermes_adapter_passes_rag_evidence():

    fake = FakeHermes()

    adapter = HermesV2Adapter(
        agent=fake
    )

    evidence = [
        {
            "document_id": "DOC-TEST",
            "title": "Test Document",
            "chunk": "Evidence test",
            "score": 0.9,
        }
    ]

    result = adapter.run(
        user_input="Apa isi dokumen?",
        session_id="test-session",
        evidence=evidence,
    )

    assert result["engine"] == "hermes"
    assert result["session_id"] == "test-session"

    assert (
        fake.received_context["knowledge_evidence"]
        == evidence
    )

    assert (
        result["reasoning"]["answer"]
        == "test reasoning"
    )


def test_hermes_adapter_returns_core_artifacts():

    fake = FakeHermes()

    adapter = HermesV2Adapter(
        agent=fake
    )

    result = adapter.run(
        user_input="halo",
        session_id="test",
        evidence=[],
    )

    assert "understanding" in result
    assert "problem" in result
    assert "reasoning" in result
'''

    if TEST.exists():
        existing = read(TEST)

        if "HermesV2Adapter" in existing:
            print("[INFO] Runtime test sudah ada.")
            return

        backup(TEST)

    write(TEST, content)


def validate_protected_files_unchanged(
    before: dict[Path, str],
) -> None:

    for path, content in before.items():
        current = read(path)

        if current != content:
            raise RuntimeError(
                f"PROTECTED FILE CHANGED: {path}"
            )

    print("[SAFETY] V1 protected files unchanged.")


def main() -> None:

    print("=" * 72)
    print("NUSANTARA V2 HERMES RUNTIME PATCH")
    print("=" * 72)

    protected_paths = [
        ROOT / "app" / "main.py",
        ROOT / "app" / "language",
        ROOT / "app" / "knowledge",
        ROOT / "app" / "problem",
    ]

    protected_files: dict[Path, str] = {}

    for path in protected_paths:
        if path.is_file():
            protected_files[path] = read(path)

    print("\n[1] Source validation")

    for path in [HERMES, ORCH, ROUTES]:
        if not path.exists():
            raise FileNotFoundError(path)

        validate_python(path)

    print("\n[2] Hermes evidence boundary")

    patch_hermes_agent()

    print("\n[3] Hermes V2 adapter")

    create_adapter()

    print("\n[4] V2 orchestrator")

    patch_v2_orchestrator()

    print("\n[5] V2 API wiring")

    patch_v2_routes()

    print("\n[6] Runtime tests")

    create_test()

    print("\n[7] Final AST validation")

    for path in [
        HERMES,
        ORCH,
        ROUTES,
        ADAPTER,
        TEST,
    ]:
        validate_python(path)

    validate_protected_files_unchanged(
        protected_files
    )

    print("\n" + "=" * 72)
    print("PATCH SUCCESS")
    print("=" * 72)

    print(
        """
Target:

/v2/chat
   |
   v
V2Orchestrator
   |
   +--> Policy
   +--> KnowledgeEngine
   |       |
   |       +--> evidence
   |
   +--> HermesV2Adapter
           |
           v
       HermesAgent
           |
           +--> LanguageEngine
           +--> ProblemEngine
           +--> ReasoningEngine
                   ^
                   |
              RAG evidence

Graphify tetap Developer Intelligence.
V1 protected core tidak disentuh.
"""
    )

    print("BACKUPS:", BACKUP_DIR)


if __name__ == "__main__":
    main()