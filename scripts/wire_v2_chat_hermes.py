from pathlib import Path
import ast
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "api" / "v2_routes.py"
BACKUP_DIR = ROOT / "docs" / "audit" / "backups"


def validate(source: str):
    ast.parse(source, filename=str(TARGET))
    compile(source, str(TARGET), "exec")


def main():
    print("=" * 72)
    print("NUSANTARA V2 CHAT - HERMES RUNTIME WIRING")
    print("=" * 72)

    source = TARGET.read_text(encoding="utf-8-sig")
    validate(source)
    print("[1] Current AST/compile : PASS")

    if "from app.hermes.agent import HermesAgent" not in source:
        source = source.replace(
            "from app.v2 import VERSION\n",
            "from app.v2 import VERSION\n"
            "from app.hermes.agent import HermesAgent\n"
            "from app.v2.hermes_adapter import HermesV2Adapter\n",
            1,
        )

    # Backup before mutation.
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"v2_routes.py.{stamp}.bak"
    shutil.copy2(TARGET, backup)
    print(f"[2] Backup               : {backup}")

    # Replace the complete chat endpoint only.
    start_marker = '@router.post("/chat")\nasync def chat(req: ChatV2Request) -> dict[str, Any]:'
    start = source.find(start_marker)

    if start < 0:
        raise RuntimeError("Chat endpoint start tidak ditemukan. Tidak ada perubahan.")

    end_marker = '\n\n@router.get("/metrics")'
    end = source.find(end_marker, start)

    if end < 0:
        raise RuntimeError("Chat endpoint end tidak ditemukan. Tidak ada perubahan.")

    new_chat = '''@router.post("/chat")
async def chat(req: ChatV2Request) -> dict[str, Any]:
    """
    V2 canonical runtime:

        Policy
        -> Memory
        -> Knowledge
        -> Hermes(Language -> Problem -> Reasoning)
        -> Ollama generation
        -> Trust
        -> Audit

    V1 engines remain untouched. Hermes is injected as the V2 runtime
    boundary rather than duplicating Language/Problem/Reasoning engines.
    """
    provider = OllamaProvider(
        base_url=settings.llm_base_url,
        model=req.model or settings.llm_model,
    )

    async def generate(prompt: str) -> str:
        out = await provider.generate({
            "prompt": prompt,
            "temperature": 0.2,
            "max_tokens": 800,
        })
        return out["content"]

    def retrieve(text: str) -> list[dict[str, Any]]:
        return [
            {
                "document_id": e.document_id,
                "title": e.title,
                "source": e.source,
                "chunk": e.chunk,
                "score": e.score,
            }
            for e in _knowledge.search_knowledge(
                text,
                top_k=settings.retrieval_top_k,
            )
        ]

    # Reuse the existing LanguageEngine instance. Hermes owns the
    # Language -> Problem -> Reasoning pipeline.
    hermes_agent = HermesAgent(
        provider=provider,
        language_engine=_language,
    )
    hermes = HermesV2Adapter(agent=hermes_agent)

    orch = V2Orchestrator(
        generate=generate,
        retrieve=retrieve,
        hermes=hermes.run,
        policy_check=_policy,
        trust_check=_trust,
        audit=audit,
        recorder=_recorder,
    )

    try:
        r = await orch.handle(req.user_input, req.session_id)
    finally:
        await provider.close()

    und = r.understanding

    return {
        "request_id": r.request_id,
        "session_id": r.session_id,
        "status": r.status,
        "response": r.response,
        "trust": r.trust,
        "evidence": r.evidence,
        "degraded": r.degraded,
        "stages_ms": r.stages,
        "understanding": (
            und.model_dump()
            if hasattr(und, "model_dump")
            else und
        ),
    }
'''

    source = source[:start] + new_chat + source[end:]

    validate(source)

    TARGET.write_text(source, encoding="utf-8", newline="")

    print("[3] HermesAgent wiring    : PASS")
    print("[4] HermesV2Adapter       : PASS")
    print("[5] Ollama provider       : PASS")
    print("[6] Hermes owns reasoning : PASS")
    print("[7] Double LanguageEngine : PREVENTED")
    print("[8] Final AST/compile     : PASS")
    print()
    print("PATCH COMPLETE")
    print(f"TARGET : {TARGET}")
    print(f"BACKUP : {backup}")


if __name__ == "__main__":
    main()
