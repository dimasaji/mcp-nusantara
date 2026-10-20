from pathlib import Path
import ast
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "hermes" / "agent.py"
BACKUP_DIR = ROOT / "docs" / "audit" / "backups"

def validate(path: Path):
    source = path.read_text(encoding="utf-8-sig")
    ast.parse(source, filename=str(path))
    compile(source, str(path), "exec")
    return source

def main():
    print("=" * 72)
    print("NUSANTARA HERMES AGENT HOTFIX")
    print("=" * 72)

    source = validate(TARGET)
    print("[1] SOURCE VALID: PASS")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"agent.py.{stamp}.bak"
    shutil.copy2(TARGET, backup)
    print(f"[2] BACKUP: {backup}")

    marker = "knowledge_evidence = []"

    if marker in source:
        print("[3] Evidence boundary already present: SKIP")
        validate(TARGET)
        return

    old_method_start = source.find("    def run(")
    if old_method_start < 0:
        raise RuntimeError("HermesAgent.run() tidak ditemukan.")

    # run() adalah method terakhir di class HermesAgent,
    # sehingga aman mengganti sampai EOF.
    prefix = source[:old_method_start]

    new_method = '''    def run(
        self,
        user_input: str,
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the Hermes reasoning pipeline.

        Evidence retrieved by the V2 runtime is passed through context
        to ReasoningEngine without changing V1 Language/Problem/Knowledge
        engines.
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

        reason = self.reasoning.process(
            problem_description=str(
                getattr(problem, "goal", None) or user_input
            ),
            context=context,
            knowledge_evidence=knowledge_evidence,
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

    ast.parse(patched, filename=str(TARGET))
    compile(patched, str(TARGET), "exec")

    TARGET.write_text(patched, encoding="utf-8", newline="")

    print("[3] Hermes evidence boundary: PASS")
    print("[4] AST validation: PASS")
    print("[5] Python compile: PASS")
    print()
    print("HOTFIX COMPLETE")
    print(f"FILE: {TARGET}")

if __name__ == "__main__":
    main()
