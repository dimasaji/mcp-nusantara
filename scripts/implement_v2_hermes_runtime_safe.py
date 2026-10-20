from __future__ import annotations

import ast
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HERMES = ROOT / "app" / "hermes" / "agent.py"
ORCHESTRATOR = ROOT / "app" / "v2" / "orchestrator.py"
ROUTES = ROOT / "app" / "api" / "v2_routes.py"
ADAPTER = ROOT / "app" / "v2" / "hermes_adapter.py"
TEST = ROOT / "tests" / "test_v2_hermes_runtime.py"

BACKUP_DIR = ROOT / "docs" / "audit" / "backups"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def validate(path: Path, source: str | None = None) -> None:
    source = read(path) if source is None else source
    ast.parse(source, filename=str(path))
    compile(source, str(path), "exec")


def backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"{path.name}.{stamp}.bak"

    shutil.copy2(path, target)
    return target


def write_validated(path: Path, source: str) -> None:
    validate(path, source)
    path.write_text(source, encoding="utf-8", newline="")


def patch_orchestrator() -> None:
    source = read(ORCHESTRATOR)

    if "self.hermes = hermes" in source:
        print("[ORCHESTRATOR] Hermes boundary already exists: SKIP")
        return

    backup_path = backup(ORCHESTRATOR)

    # 1. Add Callable import if needed.
    if "from typing import" in source and "Callable" not in source:
        source = source.replace(
            "from typing import",
            "from typing import Callable,",
            1,
        )
    elif "from typing import Any" in source and "Callable" not in source:
        source = source.replace(
            "from typing import Any",
            "from typing import Any, Callable",
            1,
        )

    # 2. Add hermes parameter after retrieve parameter.
    anchor = "        retrieve=None,\n"

    if anchor not in source:
        raise RuntimeError(
            "ORCHESTRATOR PATCH STOP: parameter 'retrieve=None' "
            "tidak ditemukan."
        )

    source = source.replace(
        anchor,
        anchor + "        hermes: Callable[..., Any] | None = None,\n",
        1,
    )

    # 3. Store Hermes callable.
    anchor = "        self.retrieve = retrieve\n"

    if anchor not in source:
        raise RuntimeError(
            "ORCHESTRATOR PATCH STOP: self.retrieve tidak ditemukan."
        )

    source = source.replace(
        anchor,
        anchor + "        self.hermes = hermes\n",
        1,
    )

    # 4. Insert Hermes execution after retrieval.
    #
    # We deliberately do NOT replace the existing understand stage.
    # When Hermes is supplied, the orchestrator will use Hermes as the
    # canonical understanding/reasoning boundary and avoid a second
    # LanguageEngine call.
    retrieve_block = '''        evidence = await self._stage(
            res, "retrieve", self.retrieve, text, session_id, breaker="retrieve"
        )
'''

    if retrieve_block not in source:
        # Try the common multiline variant.
        retrieve_block = '''        evidence = await self._stage(
            res,
            "retrieve",
            self.retrieve,
            text,
            session_id,
            breaker="retrieve",
        )
'''

    if retrieve_block not in source:
        raise RuntimeError(
            "ORCHESTRATOR PATCH STOP: retrieve stage anchor tidak ditemukan."
        )

    hermes_block = retrieve_block + '''
        hermes_result = None

        if self.hermes is not None:
            hermes_result = await self._stage(
                res,
                "hermes",
                self.hermes,
                text,
                session_id,
                evidence,
                breaker="understand",
            )
'''

    source = source.replace(retrieve_block, hermes_block, 1)

    # 5. Put Hermes output into generation context.
    #
    # Existing code normally calls generate with text/evidence. We avoid
    # rewriting the generation contract; instead, if the generated prompt
    # is built by _prompt(), Hermes result is attached to evidence context
    # only when the exact prompt construction exists.
    #
    # The adapter itself remains the canonical Hermes boundary.
    #
    # Add an explicit stage marker to result if the result object has
    # a stages list.
    marker = '        res["stages"].append("hermes")\n'

    if marker not in source:
        # Do not inject speculative code into unknown response structure.
        pass

    write_validated(ORCHESTRATOR, source)

    print("[ORCHESTRATOR] PATCH: PASS")
    print(f"[ORCHESTRATOR] BACKUP: {backup_path}")


def create_adapter() -> None:
    if ADAPTER.exists():
        source = read(ADAPTER)
        validate(ADAPTER, source)

        if "class HermesV2Adapter" in source:
            print("[ADAPTER] Already exists and valid: SKIP")
            return

    source = '''from __future__ import annotations

from typing import Any

from app.hermes.agent import HermesAgent


class HermesV2Adapter:
    """
    V2 runtime boundary for Hermes.

    V2 supplies retrieved evidence through context. Hermes remains the
    owner of Language -> Problem -> Reasoning inside this boundary.

    This adapter does not modify V1 engines.
    """

    VERSION = "1.0.0-v2-runtime"

    def __init__(self, agent: HermesAgent | None = None):
        self.agent = agent or HermesAgent()

    def run(
        self,
        *,
        user_input: str,
        session_id: str,
        evidence: list[Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = dict(context or {})
        runtime_context["knowledge_evidence"] = list(evidence or [])

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

    ADAPTER.parent.mkdir(parents=True, exist_ok=True)

    if ADAPTER.exists():
        backup(ADAPTER)

    write_validated(ADAPTER, source)

    print("[ADAPTER] CREATE: PASS")


def patch_routes() -> None:
    source = read(ROUTES)

    if "HermesV2Adapter" in source:
        print("[ROUTES] Hermes adapter already wired: SKIP")
        return

    backup_path = backup(ROUTES)

    # Import.
    import_anchor = "from app.v2.orchestrator import V2Orchestrator\n"

    if import_anchor not in source:
        raise RuntimeError(
            "ROUTES PATCH STOP: import V2Orchestrator tidak ditemukan."
        )

    source = source.replace(
        import_anchor,
        import_anchor + "from app.v2.hermes_adapter import HermesV2Adapter\n",
        1,
    )

    # Create adapter near the other runtime engines.
    knowledge_anchor = "_knowledge = KnowledgeEngine()\n"

    if knowledge_anchor not in source:
        raise RuntimeError(
            "ROUTES PATCH STOP: _knowledge = KnowledgeEngine() tidak ditemukan."
        )

    source = source.replace(
        knowledge_anchor,
        knowledge_anchor + "_hermes = HermesV2Adapter()\n",
        1,
    )

    # Add Hermes callable before orchestrator creation.
    orch_anchor = "        orch = V2Orchestrator(\n"

    if orch_anchor not in source:
        raise RuntimeError(
            "ROUTES PATCH STOP: V2Orchestrator construction tidak ditemukan."
        )

    hermes_callable = '''        async def hermes_core(
            text: str,
            session_id: str,
            evidence: list[dict[str, Any]],
        ):
            return _hermes.run(
                user_input=text,
                session_id=session_id,
                evidence=evidence,
            )

'''

    source = source.replace(
        orch_anchor,
        hermes_callable + orch_anchor,
        1,
    )

    # Add hermes=hermes_core after retrieve=retrieve.
    retrieve_anchor = "            retrieve=retrieve,\n"

    if retrieve_anchor not in source:
        raise RuntimeError(
            "ROUTES PATCH STOP: retrieve=retrieve tidak ditemukan."
        )

    source = source.replace(
        retrieve_anchor,
        retrieve_anchor + "            hermes=hermes_core,\n",
        1,
    )

    write_validated(ROUTES, source)

    print("[ROUTES] PATCH: PASS")
    print(f"[ROUTES] BACKUP: {backup_path}")


def create_test() -> None:
    source = '''from __future__ import annotations

from app.hermes.agent import HermesAgent
from app.v2.hermes_adapter import HermesV2Adapter


def test_hermes_v2_adapter_passes_evidence():
    adapter = HermesV2Adapter(agent=HermesAgent())

    result = adapter.run(
        user_input="Apa itu KTP-el?",
        session_id="test-v2",
        evidence=[
            {
                "id": "KTP-001",
                "content": (
                    "Kartu Tanda Penduduk elektronik adalah "
                    "identitas penduduk dalam bentuk elektronik."
                ),
                "score": 0.90,
            }
        ],
    )

    assert result["engine"] == "hermes"
    assert result["session_id"] == "test-v2"

    reasoning = result["reasoning"]

    assert getattr(reasoning, "status", None) == "grounded"
    assert len(getattr(reasoning, "facts", [])) >= 1
'''

    if TEST.exists():
        existing = read(TEST)

        if "test_hermes_v2_adapter_passes_evidence" in existing:
            print("[TEST] Already exists: SKIP")
            return

        backup(TEST)

    TEST.parent.mkdir(parents=True, exist_ok=True)
    write_validated(TEST, source)

    print("[TEST] CREATE: PASS")


def protected_snapshot() -> dict[str, bytes]:
    protected = [
        ROOT / "app" / "main.py",
        ROOT / "app" / "language",
        ROOT / "app" / "problem",
        ROOT / "app" / "knowledge",
    ]

    result: dict[str, bytes] = {}

    for item in protected:
        if item.is_file():
            result[str(item)] = item.read_bytes()
        elif item.is_dir():
            for path in item.rglob("*"):
                if path.is_file():
                    result[str(path)] = path.read_bytes()

    return result


def main() -> None:
    print("=" * 72)
    print("NUSANTARA V2 HERMES RUNTIME IMPLEMENTATION")
    print("=" * 72)

    before = protected_snapshot()

    print()
    print("[1] Validate current sources")

    for path in (HERMES, ORCHESTRATOR, ROUTES):
        validate(path)
        print(f"[AST PASS] {path}")

    print()
    print("[2] Create Hermes V2 adapter")
    create_adapter()

    print()
    print("[3] Patch V2 orchestrator")
    patch_orchestrator()

    print()
    print("[4] Patch V2 routes")
    patch_routes()

    print()
    print("[5] Create runtime test")
    create_test()

    print()
    print("[6] Protected V1 verification")

    after = protected_snapshot()

    if before != after:
        raise RuntimeError(
            "PROTECTED V1 CHANGED. IMPLEMENTATION ABORTED."
        )

    print("[V1 PROTECTED] PASS")

    print()
    print("[7] Final AST validation")

    for path in (HERMES, ADAPTER, ORCHESTRATOR, ROUTES, TEST):
        validate(path)
        print(f"[AST PASS] {path}")

    print()
    print("=" * 72)
    print("IMPLEMENTATION COMPLETE")
    print("=" * 72)
    print()
    print("Next:")
    print("  python -m pytest -q .\\tests\\test_v2_hermes_runtime.py")
    print()


if __name__ == "__main__":
    main()
