from pathlib import Path
import ast
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "hermes" / "agent.py"
BACKUP_DIR = ROOT / "docs" / "audit" / "backups"

def main():
    source = TARGET.read_text(encoding="utf-8-sig")

    # Pastikan source sekarang valid sebelum menyentuhnya.
    ast.parse(source, filename=str(TARGET))

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"agent.py.{stamp}.bak"
    shutil.copy2(TARGET, backup)

    start = source.find("    def run(")
    if start < 0:
        raise RuntimeError("HermesAgent.run() tidak ditemukan.")

    prefix = source[:start]

    new_method = '''    def run(
        self,
        user_input: str,
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the Hermes pipeline using the existing ReasoningEngine API.

        Evidence from V2 is passed through context["knowledge_evidence"].
        No V1 Language, Problem, or Knowledge engine is modified.
        """
        understood = self.language.process(user_input)

        problem = self.problem.analyze(
            user_input=user_input,
            context=context,
        )

        knowledge_evidence = []

        if isinstance(context, dict):
            candidate_evidence = context.get("knowledge_evidence", [])

            if isinstance(candidate_evidence, list):
                knowledge_evidence = candidate_evidence

        intent_name = ""
        intent_confidence = 0.0

        if isinstance(understood, dict):
            intent_name = str(
                understood.get("intent_name")
                or understood.get("intent")
                or ""
            )

            try:
                intent_confidence = float(
                    understood.get("intent_confidence", 0.0) or 0.0
                )
            except (TypeError, ValueError):
                intent_confidence = 0.0
        else:
            intent_name = str(
                getattr(understood, "intent_name", None)
                or getattr(understood, "intent", None)
                or ""
            )

            try:
                intent_confidence = float(
                    getattr(understood, "intent_confidence", 0.0)
                    or 0.0
                )
            except (TypeError, ValueError):
                intent_confidence = 0.0

        reason = self.reasoning.analyze(
            user_input=user_input,
            evidence=knowledge_evidence,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
        )

        return {
            "session_id": session_id,
            "understanding": (
                understood.model_dump()
                if hasattr(understood, "model_dump")
                else understood
            ),
            "problem": (
                problem.model_dump()
                if hasattr(problem, "model_dump")
                else problem
            ),
            "reasoning": (
                reason.model_dump()
                if hasattr(reason, "model_dump")
                else reason
            ),
        }
'''

    patched = prefix + new_method

    # Validasi sebelum write.
    ast.parse(patched, filename=str(TARGET))
    compile(patched, str(TARGET), "exec")

    TARGET.write_text(patched, encoding="utf-8", newline="")

    print("=" * 72)
    print("HERMES REASONING API FIX")
    print("=" * 72)
    print("BACKUP :", backup)
    print("TARGET :", TARGET)
    print("AST    : PASS")
    print("COMPILE: PASS")
    print()
    print("ReasoningEngine.analyze() digunakan.")
    print("Tidak ada perubahan pada V1 engines.")

if __name__ == "__main__":
    main()
