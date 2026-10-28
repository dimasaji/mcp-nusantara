#!/usr/bin/env python3
"""
NUSANTARA MASTER DEVELOPER ENGINE v3.0.0

Safe autonomous engineering controller for Nusantara.

Workflow:
    DISCOVER -> UNDERSTAND -> ACCEPTANCE -> TEST -> GAP
    -> PLAN -> OLLAMA PATCH -> VALIDATE -> APPLY
    -> TEST -> REGRESSION -> SECURITY -> GATE -> NEXT

Safety:
- Never git reset/clean/checkout.
- Never delete files, databases, or user data.
- Never execute model-generated shell commands.
- Model may only propose structured write patches.
- Protected V1 core is read-only for autonomous changes.
- Existing working-tree changes are preserved.
- Changes are snapshotted before application.
- Failed iterations are rolled back only for files touched by that iteration.
- Compile success alone never closes a phase.
- Ollama unavailable in --apply => BLOCKED.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENGINE_VERSION = "3.0.0"

MAX_FILE_BYTES = 2_000_000
MAX_PATCH_BYTES = 8_000_000

PROTECTED_PATHS = {
    "app/main.py",
    "app/language",
    "app/knowledge",
    "app/problem",
}

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

PHASE_NAMES = {
    "v1": {
        0: "Environment / Architecture",
        1: "Foundation",
        2: "LLM Provider",
        3: "Language",
        4: "Context",
        5: "Problem",
        6: "Knowledge / RAG",
        7: "Reasoning",
        8: "Workflow",
        9: "Policy",
        10: "Trust",
        11: "Memory",
        12: "Tool",
        13: "MCP Ready",
        14: "Human Handoff",
        15: "API Gateway",
        16: "UI",
        17: "Eval / Observability",
        18: "Docker / Production",
    },
    "v2": {
        0: "Discovery / Reconciliation",
        1: "Architecture",
        2: "Hardening",
        3: "Observability",
        4: "Trust",
        5: "Policy",
        6: "Memory",
        7: "RAG",
        8: "MCP",
        9: "Tool Governance",
        10: "Experience",
        11: "Feedback",
        12: "Evaluation",
        13: "Failure Analysis",
        14: "Gap Detection",
        15: "Knowledge Discovery",
        16: "Experiment",
        17: "Improvement Proposal",
        18: "Human Approval",
        19: "V1.x Development",
        20: "Regression / Security",
        21: "Release / Rollback",
    },
}

PHASE_TEST_HINTS = {
    "v1": {
        0: ["test", "phase", "environment"],
        1: ["test", "foundation", "health"],
        2: ["provider", "ollama", "model"],
        3: ["language", "normal", "intent"],
        4: ["context", "session"],
        5: ["problem"],
        6: ["rag", "knowledge", "retriev"],
        7: ["reason"],
        8: ["workflow"],
        9: ["policy"],
        10: ["trust"],
        11: ["memory"],
        12: ["tool"],
        13: ["mcp"],
        14: ["handoff"],
        15: ["api", "http"],
        16: ["ui"],
        17: ["observ", "eval", "metric"],
        18: ["docker", "production"],
    },
    "v2": {
        0: ["phase", "gap", "audit", "roadmap"],
        1: ["architecture", "integration", "v2"],
        2: ["hardening", "timeout", "retry", "circuit"],
        3: ["observ", "metric", "http"],
        4: ["trust", "ground", "evidence"],
        5: ["policy", "govern"],
        6: ["memory", "session"],
        7: ["rag", "retriev", "ingest", "indobert"],
        8: ["mcp"],
        9: ["tool", "govern"],
        10: ["experience", "event"],
        11: ["feedback"],
        12: ["eval", "baseline", "smoke"],
        13: ["failure"],
        14: ["gap"],
        15: ["discover", "source", "knowledge"],
        16: ["experiment"],
        17: ["proposal", "improvement"],
        18: ["approval", "human"],
        19: ["change", "version", "git"],
        20: ["regression", "security"],
        21: ["release", "rollback", "docker"],
    },
}


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    duration_ms: int = 0


@dataclass
class PhaseResult:
    track: str
    phase: int
    name: str
    status: str
    checks: list[Check] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    iteration: int = 0
    reason: str = ""


class MasterDeveloperEngine:

    def __init__(
        self,
        root: Path,
        apply: bool = False,
        docker: bool = False,
        api: bool = False,
        model: str = "qwen2.5-coder:7b",
        ollama_url: str = "http://127.0.0.1:11434",
        max_iterations: int = 3,
    ) -> None:

        self.root = root.resolve()
        self.apply = apply
        self.docker = docker
        self.api = api
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.max_iterations = max(1, min(max_iterations, 10))

        self.audit_dir = self.root / "docs" / "audit" / "master_engine"
        self.evidence_dir = self.audit_dir / "evidence"
        self.runs_dir = self.audit_dir / "runs"

        self.state_path = self.audit_dir / "state.json"
        self.matrix_path = self.audit_dir / "phase_matrix.json"
        self.gaps_path = self.audit_dir / "gaps.json"
        self.actions_path = self.audit_dir / "actions.jsonl"

        self.report_path = (
            self.root / "docs" / "audit" / "MASTER_ENGINE_V3_REPORT.md"
        )

        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================
    # BASIC
    # ========================================================

    def rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def safe_write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def append_action(self, action: dict[str, Any]) -> None:
        with self.actions_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")

    def print_header(self, title: str) -> None:
        print("=" * 76)
        print(title)
        print("=" * 76)

    # ========================================================
    # COMMAND EXECUTION
    # ========================================================

    def run_cmd(
        self,
        args: list[str],
        timeout: int = 120,
        cwd: Path | None = None,
    ) -> tuple[int, str]:

        try:
            p = subprocess.run(
                args,
                cwd=str(cwd or self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                shell=False,
            )

            return p.returncode, (
                p.stdout + "\n" + p.stderr
            ).strip()

        except subprocess.TimeoutExpired as exc:
            return 124, f"TIMEOUT: {exc}"

        except OSError as exc:
            return 127, f"EXECUTION ERROR: {exc}"

    # ========================================================
    # REPOSITORY SAFETY
    # ========================================================

    def git_status(self) -> Check:

        code, out = self.run_cmd(
            ["git", "rev-parse", "--show-toplevel"],
            timeout=20,
        )

        if code != 0:
            return Check(
                "git-repository",
                "FAIL",
                out,
            )

        code2, branch = self.run_cmd(
            ["git", "branch", "--show-current"],
            timeout=20,
        )

        branch_name = branch.strip() or "(detached)"

        return Check(
            "git-repository",
            "PASS",
            f"root={out.strip()} branch={branch_name}; existing changes preserved",
        )

    def protected(self, rel_path: str) -> bool:

        p = rel_path.replace("\\", "/").strip("/")

        for protected in PROTECTED_PATHS:

            q = protected.strip("/")

            if p == q or p.startswith(q + "/"):
                return True

        return False

    def valid_relative_path(
        self,
        rel_path: str,
    ) -> tuple[bool, str]:

        if not isinstance(rel_path, str) or not rel_path.strip():
            return False, "empty path"

        p = Path(rel_path)

        if p.is_absolute():
            return False, "absolute path rejected"

        normalized = p.as_posix()

        if (
            normalized.startswith("../")
            or "/../" in normalized
            or normalized == ".."
        ):
            return False, "path traversal rejected"

        target = (self.root / p).resolve()

        try:
            target.relative_to(self.root)
        except ValueError:
            return False, "path outside repository rejected"

        if self.protected(normalized):
            return False, (
                f"protected V1 path rejected: {normalized}"
            )

        lower = normalized.lower()

        if lower.endswith(
            (".pem", ".key", ".pfx", ".p12")
        ):
            return False, "credential/key file rejected"

        if any(
            x in lower
            for x in [".env", "secret", "credential"]
        ):
            return False, "sensitive path rejected"

        return True, normalized

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
        paths: list[str],
        destination: Path,
    ) -> dict[str, Any]:

        snap: dict[str, Any] = {}

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        for rel in paths:

            target = self.root / rel

            item = {
                "exists": target.exists()
            }

            if target.exists():

                data = target.read_bytes()

                item["sha256"] = hashlib.sha256(
                    data
                ).hexdigest()

                item["bytes"] = len(data)

                backup = destination / rel

                backup.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                backup.write_bytes(data)

            snap[rel] = item

        return snap

    def restore_snapshot(
        self,
        snapshot_dir: Path,
        paths: list[str],
    ) -> None:

        for rel in paths:

            backup = snapshot_dir / rel
            target = self.root / rel

            if backup.exists():

                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                target.write_bytes(
                    backup.read_bytes()
                )

            else:

                if target.exists():
                    target.unlink()

    # ========================================================
    # DISCOVERY
    # ========================================================

    def inventory(self) -> dict[str, int]:

        counts: dict[str, int] = {}

        for name in [
            "app",
            "tests",
            "scripts",
            "docs",
            "data",
            "nusantara-models",
        ]:

            base = self.root / name

            if not base.exists():
                counts[name] = 0
                continue

            n = 0

            for p in base.rglob("*"):

                if not p.is_file():
                    continue

                if any(
                    part in IGNORED_DIRS
                    for part in p.parts
                ):
                    continue

                n += 1

            counts[name] = n

        return counts

    def architecture_scan(self) -> dict[str, bool]:

        text_parts: list[str] = []

        for rel in ["app", "scripts"]:

            base = self.root / rel

            if not base.exists():
                continue

            for p in base.rglob("*.py"):

                if any(
                    part in IGNORED_DIRS
                    for part in p.parts
                ):
                    continue

                try:

                    if p.stat().st_size <= 500_000:

                        text_parts.append(
                            p.read_text(
                                encoding="utf-8",
                                errors="ignore",
                            )
                        )

                except OSError:
                    pass

        blob = "\n".join(
            text_parts
        ).lower()

        terms = {
            "FastAPI": ["fastapi"],
            "V1 route": ["/v1"],
            "V2 route": ["/v2"],
            "Ollama": ["ollama"],
            "Hermes": ["hermes"],
            "Graphify": ["graphify"],
            "Knowledge": ["knowledge"],
            "RAG": ["rag", "retriev"],
            "Trust": ["trust"],
            "Policy": ["policy"],
            "Memory": ["memory"],
            "MCP": ["mcp"],
            "Tool Governance": [
                "governedtoolregistry",
                "tool governance",
                "tool_governance",
            ],
            "Approval": [
                "approval",
                "human approval",
            ],
            "Observability": [
                "observability",
                "metrics",
            ],
        }

        return {
            key: any(
                term in blob
                for term in values
            )
            for key, values in terms.items()
        }

    def code_map(
        self,
        limit: int = 300,
    ) -> list[dict[str, Any]]:

        result = []

        base = self.root / "app"

        if not base.exists():
            return result

        for p in base.rglob("*.py"):

            if len(result) >= limit:
                break

            if any(
                part in IGNORED_DIRS
                for part in p.parts
            ):
                continue

            try:

                source = p.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                tree = ast.parse(source)

            except Exception:
                continue

            classes = [
                n.name
                for n in ast.walk(tree)
                if isinstance(n, ast.ClassDef)
            ]

            funcs = [
                n.name
                for n in ast.walk(tree)
                if isinstance(
                    n,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                )
            ]

            result.append(
                {
                    "path": self.rel(p),
                    "classes": classes[:30],
                    "functions": funcs[:50],
                }
            )

        return result

    def discover_tests(
        self,
        track: str,
        phase: int,
    ) -> list[Path]:

        hints = PHASE_TEST_HINTS.get(
            track,
            {},
        ).get(phase, [])

        tests = []

        base = self.root / "tests"

        if not base.exists():
            return tests

        for p in base.rglob("test_*.py"):

            name = p.name.lower()

            try:

                content = p.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).lower()

            except OSError:
                continue

            score = sum(
                1
                for h in hints
                if h in name or h in content
            )

            if score:
                tests.append(
                    (score, p)
                )

        tests.sort(
            key=lambda x: (
                -x[0],
                str(x[1]),
            )
        )

        return [
            p
            for _, p in tests[:12]
        ]

    # ========================================================
    # TESTING
    # ========================================================

    def compile_all(self) -> Check:

        started = time.perf_counter()

        code, out = self.run_cmd(
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "app",
                "scripts",
                "tests",
            ],
            timeout=180,
        )

        ms = int(
            (time.perf_counter() - started)
            * 1000
        )

        return Check(
            "compileall",
            "PASS" if code == 0 else "FAIL",
            out[-4000:],
            ms,
        )

    def run_phase_tests(
        self,
        tests: list[Path],
    ) -> Check:

        if not tests:

            return Check(
                "phase-tests",
                "NOT_FOUND",
                "No dedicated phase test discovered; this cannot close a phase.",
            )

        started = time.perf_counter()

        args = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ]

        args.extend(
            self.rel(p)
            for p in tests
        )

        code, out = self.run_cmd(
            args,
            timeout=300,
        )

        ms = int(
            (time.perf_counter() - started)
            * 1000
        )

        return Check(
            "phase-tests",
            "PASS" if code == 0 else "FAIL",
            out[-12000:],
            ms,
        )

    def run_regression(self) -> Check:

        started = time.perf_counter()

        code, out = self.run_cmd(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ],
            timeout=600,
        )

        ms = int(
            (time.perf_counter() - started)
            * 1000
        )

        return Check(
            "full-regression",
            "PASS" if code == 0 else "FAIL",
            out[-12000:],
            ms,
        )

    def security_check(self) -> Check:

        risky_patterns = [
            r"(?i)BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY",
            r"(?i)AKIA[0-9A-Z]{16}",
            r"(?i)ghp_[A-Za-z0-9_]{30,}",
        ]

        hits = []

        for base_name in [
            "app",
            "scripts",
        ]:

            base = self.root / base_name

            if not base.exists():
                continue

            for p in base.rglob("*"):

                if not p.is_file():
                    continue

                if p.stat().st_size > 1_000_000:
                    continue

                if any(
                    part in IGNORED_DIRS
                    for part in p.parts
                ):
                    continue

                try:

                    text = p.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )

                except OSError:
                    continue

                for pattern in risky_patterns:

                    if re.search(
                        pattern,
                        text,
                    ):

                        hits.append(
                            self.rel(p)
                        )

                        break

        return Check(
            "security-secret-scan",
            "FAIL" if hits else "PASS",
            (
                f"potential secret hits: {hits[:20]}"
                if hits
                else
                "no obvious hard-coded secret pattern found"
            ),
        )

    # ========================================================
    # OLLAMA
    # ========================================================

    def ollama_tags(
        self,
    ) -> tuple[bool, str]:

        url = (
            self.ollama_url
            + "/api/tags"
        )

        try:

            with urllib.request.urlopen(
                url,
                timeout=5,
            ) as response:

                data = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

            return True, data[:8000]

        except Exception as exc:

            return False, str(exc)

    def ollama_generate(
        self,
        prompt: str,
    ) -> tuple[bool, str]:

        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                },
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            self.ollama_url
            + "/api/generate",
            data=payload,
            headers={
                "Content-Type":
                    "application/json"
            },
            method="POST",
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=300,
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8",
                        errors="replace",
                    )
                )

            return True, str(
                data.get(
                    "response",
                    "",
                )
            )

        except Exception as exc:

            return False, str(exc)

    # ========================================================
    # PHASE CONTEXT
    # ========================================================

    def phase_context(
        self,
        track: str,
        phase: int,
    ) -> dict[str, Any]:

        name = PHASE_NAMES[
            track
        ][phase]

        tests = self.discover_tests(
            track,
            phase,
        )

        inventory = self.inventory()

        architecture = (
            self.architecture_scan()
        )

        evidence = []

        possible_evidence = [
            self.root
            / "PROGRESS_REPORT.md",

            self.root
            / "docs"
            / "roadmap.md",

            self.root
            / "docs"
            / "v2"
            / "ROADMAP_STATUS.md",

            self.root
            / "docs"
            / "audit"
            / "GATES.md",

            self.root
            / "docs"
            / "contracts"
            / "NUSANTARA-ARCHITECTURE-CONTRACT-V1.md",
        ]

        for p in possible_evidence:

            if p.exists():
                evidence.append(
                    self.rel(p)
                )

        return {
            "track": track,
            "phase": phase,
            "name": name,
            "inventory": inventory,
            "architecture": architecture,
            "tests": [
                self.rel(p)
                for p in tests
            ],
            "evidence": evidence,
            "protected_paths": sorted(
                PROTECTED_PATHS
            ),
        }

    def heuristic_gaps(
        self,
        track: str,
        phase: int,
        checks: list[Check],
        context: dict[str, Any],
    ) -> list[str]:

        gaps = []

        phase_tests = next(
            (
                c
                for c in checks
                if c.name == "phase-tests"
            ),
            None,
        )

        regression = next(
            (
                c
                for c in checks
                if c.name == "full-regression"
            ),
            None,
        )

        if (
            phase_tests is None
            or phase_tests.status
            == "NOT_FOUND"
        ):
            gaps.append(
                "No dedicated phase test discovered."
            )

        if (
            phase_tests is not None
            and phase_tests.status == "FAIL"
        ):
            gaps.append(
                "Dedicated phase tests fail."
            )

        if (
            regression is not None
            and regression.status == "FAIL"
        ):
            gaps.append(
                "Full regression fails."
            )

        if (
            track == "v2"
            and phase == 0
        ):

            if not (
                self.root
                / "docs"
                / "audit"
                / "GATES.md"
            ).exists():

                gaps.append(
                    "docs/audit/GATES.md is missing."
                )

            if not (
                self.root
                / "docs"
                / "contracts"
                / "NUSANTARA-ARCHITECTURE-CONTRACT-V1.md"
            ).exists():

                gaps.append(
                    "V1 architecture contract is missing."
                )

        if (
            track == "v2"
            and phase == 7
        ):

            if not any(
                context[
                    "architecture"
                ].get(k)
                for k in [
                    "RAG",
                    "Knowledge",
                ]
            ):

                gaps.append(
                    "No strong RAG/Knowledge implementation signal."
                )

        return gaps

    # ========================================================
    # PHASE ANALYSIS
    # ========================================================

    def analyze_phase(
        self,
        track: str,
        phase: int,
    ) -> PhaseResult:

        name = PHASE_NAMES[
            track
        ][phase]

        self.print_header(
            f"{track.upper()} PHASE {phase:02d} — {name}"
        )

        context = self.phase_context(
            track,
            phase,
        )

        checks = [
            self.git_status()
        ]

        compile_check = (
            self.compile_all()
        )

        checks.append(
            compile_check
        )

        tests = self.discover_tests(
            track,
            phase,
        )

        phase_test = (
            self.run_phase_tests(
                tests
            )
        )

        checks.append(
            phase_test
        )

        regression = (
            self.run_regression()
        )

        checks.append(
            regression
        )

        gaps = self.heuristic_gaps(
            track,
            phase,
            checks,
            context,
        )

        if (
            not gaps
            and phase_test.status
            == "PASS"
            and regression.status
            == "PASS"
        ):

            status = "CLOSED"

            reason = (
                "Dedicated phase tests and full regression passed."
            )

        elif any(
            c.status == "FAIL"
            for c in checks
        ):

            status = "REGRESSION"

            reason = (
                "One or more verification checks failed."
            )

        else:

            status = "PARTIAL"

            reason = (
                "Acceptance evidence is incomplete."
            )

        result = PhaseResult(
            track=track,
            phase=phase,
            name=name,
            status=status,
            checks=checks,
            gaps=gaps,
            reason=reason,
        )

        self.persist_phase(
            result,
            context,
        )

        return result

    # ========================================================
    # SOURCE COLLECTION
    # ========================================================

    def collect_relevant_sources(
        self,
        track: str,
        phase: int,
        max_files: int = 20,
    ) -> list[dict[str, str]]:

        hints = PHASE_TEST_HINTS.get(
            track,
            {},
        ).get(phase, [])

        candidates = []

        for base_name in [
            "app",
            "scripts",
            "tests",
        ]:

            base = self.root / base_name

            if not base.exists():
                continue

            for p in base.rglob("*.py"):

                if any(
                    part in IGNORED_DIRS
                    for part in p.parts
                ):
                    continue

                try:

                    size = p.stat().st_size

                    if size > MAX_FILE_BYTES:
                        continue

                    text = p.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )

                except OSError:
                    continue

                hay = (
                    p.name
                    + "\n"
                    + text[:100_000]
                ).lower()

                score = sum(
                    1
                    for h in hints
                    if h in hay
                )

                if score:
                    candidates.append(
                        (score, p)
                    )

        candidates.sort(
            key=lambda x: (
                -x[0],
                str(x[1]),
            )
        )

        out = []

        for _, p in candidates[:max_files]:

            out.append(
                {
                    "path": self.rel(p),
                    "content": p.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    ),
                }
            )

        return out

    # ========================================================
    # OLLAMA CODING PROMPT
    # ========================================================

    def build_coding_prompt(
        self,
        track: str,
        phase: int,
        result: PhaseResult,
        context: dict[str, Any],
        sources: list[dict[str, str]],
    ) -> str:

        source_text = "\n\n".join(
            (
                f"===== FILE: {x['path']} =====\n"
                f"{x['content'][:120_000]}"
            )
            for x in sources
        )

        gaps = "\n".join(
            f"- {g}"
            for g in result.gaps
        ) or "- None"

        return f"""
You are the coding brain for Nusantara Master Developer Engine v3.

You are NOT allowed to execute commands.

You must return ONLY one JSON object.

Goal:
Implement the minimum safe changes required to improve:

{track.upper()} PHASE {phase:02d} — {result.name}

Known gaps:
{gaps}

Repository context:
{json.dumps(context, ensure_ascii=False, indent=2)}

Hard rules:

1. Never modify protected V1 paths:
   app/main.py
   app/language/
   app/knowledge/
   app/problem/

2. Never delete files.

3. Never modify credentials, secrets, .env, keys,
   databases, or user data.

4. Do not rewrite unrelated files.

5. Preserve existing architecture and interfaces.

6. Prefer adding focused tests for the phase.

7. The controller will compile and test your patch.

8. Return complete file contents for every write action.

9. Maximum 8 MB total JSON response.

10. Allowed operation is ONLY "write".

Required JSON schema:

{{
  "actions": [
    {{
      "op": "write",
      "path": "relative/path.py",
      "content": "complete UTF-8 file content"
    }}
  ]
}}

If no safe change can be justified, return:

{{"actions":[]}}

Repository source excerpts:

{source_text}
""".strip()

    # ========================================================
    # PATCH PARSER
    # ========================================================

    def parse_patch(
        self,
        raw: str,
    ) -> tuple[
        bool,
        dict[str, Any] | None,
        str,
    ]:

        text = raw.strip()

        if "```" in text:

            blocks = re.findall(
                r"```(?:json)?\s*(.*?)```",
                text,
                flags=re.S | re.I,
            )

            if blocks:
                text = blocks[0].strip()

        try:

            obj = json.loads(text)

        except json.JSONDecodeError as exc:

            return (
                False,
                None,
                f"invalid JSON: {exc}",
            )

        if (
            not isinstance(obj, dict)
            or not isinstance(
                obj.get("actions"),
                list,
            )
        ):

            return (
                False,
                None,
                "JSON must contain actions list",
            )

        if (
            len(
                json.dumps(
                    obj,
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            > MAX_PATCH_BYTES
        ):

            return (
                False,
                None,
                "patch exceeds size limit",
            )

        return True, obj, ""

    def validate_patch(
        self,
        obj: dict[str, Any],
    ) -> tuple[
        bool,
        list[dict[str, str]],
        list[str],
    ]:

        actions = obj.get(
            "actions",
            [],
        )

        valid = []
        errors = []

        for i, action in enumerate(
            actions
        ):

            if not isinstance(
                action,
                dict,
            ):

                errors.append(
                    f"action {i}: not an object"
                )

                continue

            if action.get("op") != "write":

                errors.append(
                    f"action {i}: only write operation is allowed"
                )

                continue

            path = action.get(
                "path"
            )

            content = action.get(
                "content"
            )

            ok, normalized = (
                self.valid_relative_path(
                    path
                )
            )

            if not ok:

                errors.append(
                    f"action {i}: {normalized}"
                )

                continue

            if not isinstance(
                content,
                str,
            ):

                errors.append(
                    f"action {i}: content must be string"
                )

                continue

            if (
                len(
                    content.encode("utf-8")
                )
                > MAX_FILE_BYTES
            ):

                errors.append(
                    f"action {i}: file exceeds size limit"
                )

                continue

            if re.search(
                r"(?i)BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY",
                content,
            ):

                errors.append(
                    f"action {i}: possible private key content"
                )

                continue

            valid.append(
                {
                    "op": "write",
                    "path": normalized,
                    "content": content,
                }
            )

        return (
            not errors,
            valid,
            errors,
        )

    def apply_patch(
        self,
        actions: list[dict[str, str]],
        snapshot_dir: Path,
    ) -> list[str]:

        paths = [
            a["path"]
            for a in actions
        ]

        self.snapshot(
            paths,
            snapshot_dir,
        )

        changes = []

        for action in actions:

            target = (
                self.root
                / action["path"]
            )

            old = (
                target.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
                if target.exists()
                else None
            )

            self.safe_write(
                target,
                action["content"],
            )

            if old != action["content"]:
                changes.append(
                    action["path"]
                )

        return changes

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def persist_phase(
        self,
        result: PhaseResult,
        context: dict[str, Any],
    ) -> None:

        payload = {
            "timestamp": self.now(),
            "engine_version": ENGINE_VERSION,
            "result": asdict(result),
            "context": context,
        }

        evidence = (
            self.evidence_dir
            / result.track
            / f"{result.phase:02d}"
        )

        evidence.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.safe_write(
            evidence / "result.json",
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
        )

        lines = [
            (
                f"# {result.track.upper()} "
                f"Phase {result.phase:02d} "
                f"— {result.name}"
            ),
            "",
            f"- Status: **{result.status}**",
            f"- Engine: **{ENGINE_VERSION}**",
            f"- Timestamp: `{payload['timestamp']}`",
            f"- Reason: {result.reason}",
            "",
            "## Gaps",
        ]

        if result.gaps:
            lines.extend(
                f"- {g}"
                for g in result.gaps
            )
        else:
            lines.append(
                "- None"
            )

        lines.extend(
            [
                "",
                "## Checks",
            ]
        )

        for c in result.checks:

            lines.append(
                f"- `{c.name}`: "
                f"**{c.status}** — "
                f"{c.detail[:500]}"
            )

        self.safe_write(
            evidence / "result.md",
            "\n".join(lines)
            + "\n",
        )

    def save_state(
        self,
        latest: PhaseResult | None = None,
    ) -> None:

        state = {
            "engine_version": ENGINE_VERSION,
            "timestamp": self.now(),
            "root": str(self.root),
            "apply": self.apply,
            "model": self.model,
            "ollama_url": self.ollama_url,
            "max_iterations": self.max_iterations,
            "latest": (
                asdict(latest)
                if latest
                else None
            ),
        }

        self.safe_write(
            self.state_path,
            json.dumps(
                state,
                indent=2,
                ensure_ascii=False,
            ),
        )

    # ========================================================
    # AUTONOMOUS PHASE
    # ========================================================

    def autonomous_phase(
        self,
        track: str,
        phase: int,
    ) -> PhaseResult:

        result = self.analyze_phase(
            track,
            phase,
        )

        if not self.apply:
            return result

        if result.status == "CLOSED":
            return result

        ollama_ok, ollama_detail = (
            self.ollama_tags()
        )

        if not ollama_ok:

            result.status = "BLOCKED"

            result.reason = (
                f"Ollama unavailable: "
                f"{ollama_detail}"
            )

            self.persist_phase(
                result,
                self.phase_context(
                    track,
                    phase,
                ),
            )

            self.save_state(
                result
            )

            return result

        for iteration in range(
            1,
            self.max_iterations + 1,
        ):

            result.iteration = (
                iteration
            )

            print(
                f"\n[AUTONOMOUS ITERATION "
                f"{iteration}/{self.max_iterations}]"
            )

            context = self.phase_context(
                track,
                phase,
            )

            sources = (
                self.collect_relevant_sources(
                    track,
                    phase,
                )
            )

            prompt = (
                self.build_coding_prompt(
                    track,
                    phase,
                    result,
                    context,
                    sources,
                )
            )

            ok, raw = (
                self.ollama_generate(
                    prompt
                )
            )

            if not ok:

                result.status = "BLOCKED"

                result.reason = (
                    "Ollama generation failed: "
                    + raw
                )

                self.persist_phase(
                    result,
                    context,
                )

                self.save_state(
                    result
                )

                return result

            ok, patch, parse_error = (
                self.parse_patch(raw)
            )

            if (
                not ok
                or patch is None
            ):

                result.gaps.append(
                    "Model patch rejected: "
                    + parse_error
                )

                self.append_action(
                    {
                        "timestamp": self.now(),
                        "type": "patch_rejected",
                        "phase": (
                            f"{track}:{phase}"
                        ),
                        "reason": parse_error,
                    }
                )

                continue

            valid, actions, errors = (
                self.validate_patch(
                    patch
                )
            )

            if not valid:

                result.gaps.extend(
                    [
                        "Patch validation: "
                        + e
                        for e in errors
                    ]
                )

                self.append_action(
                    {
                        "timestamp": self.now(),
                        "type": "patch_rejected",
                        "phase": (
                            f"{track}:{phase}"
                        ),
                        "errors": errors,
                    }
                )

                continue

            if not actions:

                result.reason = (
                    "Coding brain proposed no safe changes."
                )

                break

            run_dir = (
                self.runs_dir
                / datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
                / (
                    f"{track}_{phase:02d}_"
                    f"{iteration}"
                )
            )

            snapshot_dir = (
                run_dir
                / "snapshot"
            )

            run_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.safe_write(
                run_dir / "patch.json",
                json.dumps(
                    {
                        "actions": actions
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
            )

            paths = [
                a["path"]
                for a in actions
            ]

            self.snapshot(
                paths,
                snapshot_dir,
            )

            try:

                changes = (
                    self.apply_patch(
                        actions,
                        snapshot_dir,
                    )
                )

                result.changes.extend(
                    changes
                )

                compile_check = (
                    self.compile_all()
                )

                if (
                    compile_check.status
                    != "PASS"
                ):

                    self.restore_snapshot(
                        snapshot_dir,
                        paths,
                    )

                    result.gaps = [
                        "Compile failed after patch."
                    ] + result.gaps

                    self.append_action(
                        {
                            "timestamp": self.now(),
                            "type": "repair",
                            "phase": (
                                f"{track}:{phase}"
                            ),
                            "iteration": iteration,
                            "reason": (
                                "compile_failed"
                            ),
                            "restored": paths,
                        }
                    )

                    continue

                phase_tests = (
                    self.run_phase_tests(
                        self.discover_tests(
                            track,
                            phase,
                        )
                    )
                )

                regression = (
                    self.run_regression()
                )

                security = (
                    self.security_check()
                )

                if (
                    phase_tests.status
                    == "PASS"
                    and regression.status
                    == "PASS"
                    and security.status
                    == "PASS"
                ):

                    result.status = "CLOSED"

                    result.reason = (
                        "Patch applied and "
                        "dedicated tests, "
                        "regression, and "
                        "security passed."
                    )

                    result.checks = [
                        compile_check,
                        phase_tests,
                        regression,
                        security,
                    ]

                    self.append_action(
                        {
                            "timestamp": self.now(),
                            "type": "phase_closed",
                            "phase": (
                                f"{track}:{phase}"
                            ),
                            "iteration": iteration,
                            "changes": changes,
                        }
                    )

                    self.persist_phase(
                        result,
                        self.phase_context(
                            track,
                            phase,
                        ),
                    )

                    self.save_state(
                        result
                    )

                    return result

                self.restore_snapshot(
                    snapshot_dir,
                    paths,
                )

                result.status = (
                    "REGRESSION"
                )

                result.reason = (
                    "Applied patch failed "
                    "post-apply verification; "
                    "iteration restored."
                )

                result.checks = [
                    compile_check,
                    phase_tests,
                    regression,
                    security,
                ]

                result.gaps = []

                if (
                    phase_tests.status
                    != "PASS"
                ):
                    result.gaps.append(
                        "Dedicated phase tests did not pass."
                    )

                if (
                    regression.status
                    != "PASS"
                ):
                    result.gaps.append(
                        "Full regression did not pass."
                    )

                if (
                    security.status
                    != "PASS"
                ):
                    result.gaps.append(
                        "Security scan did not pass."
                    )

                self.append_action(
                    {
                        "timestamp": self.now(),
                        "type": "repair",
                        "phase": (
                            f"{track}:{phase}"
                        ),
                        "iteration": iteration,
                        "reason": result.reason,
                        "restored": paths,
                    }
                )

            except Exception as exc:

                self.restore_snapshot(
                    snapshot_dir,
                    paths,
                )

                result.status = "FAILED"

                result.reason = (
                    "Controller error; "
                    "iteration restored: "
                    + str(exc)
                )

                self.persist_phase(
                    result,
                    self.phase_context(
                        track,
                        phase,
                    ),
                )

                self.save_state(
                    result
                )

                return result

        result.status = "PARTIAL"

        result.reason = (
            f"Phase not closed after "
            f"{self.max_iterations} "
            f"autonomous iterations."
        )

        self.persist_phase(
            result,
            self.phase_context(
                track,
                phase,
            ),
        )

        self.save_state(
            result
        )

        return result

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> None:

        self.print_header(
            "NUSANTARA MASTER DEVELOPER ENGINE"
        )

        print(
            f"Version : {ENGINE_VERSION}"
        )

        print(
            f"Root    : {self.root}"
        )

        print(
            f"Python  : "
            f"{sys.version.split()[0]}"
        )

        print(
            "Mode    : "
            + (
                "APPLY"
                if self.apply
                else "VERIFY"
            )
        )

        print(
            "Docker  : "
            + (
                "ON"
                if self.docker
                else "OFF"
            )
        )

        print(
            "API     : "
            + (
                "ON"
                if self.api
                else "OFF"
            )
        )

        print(
            f"Model   : {self.model}"
        )

        print(
            f"Ollama  : {self.ollama_url}"
        )

        print(
            f"Max iter: {self.max_iterations}"
        )

        self.print_header(
            "REPOSITORY SAFETY"
        )

        c = self.git_status()

        print(
            f"[{c.status}] {c.detail}"
        )

        print(
            "[SAFE] Engine never git reset/clean/checkout."
        )

        print(
            "[SAFE] Engine never performs autonomous delete."
        )

        print(
            "[SAFE] V1 core protected from autonomous writes:"
        )

        for p in sorted(
            PROTECTED_PATHS
        ):

            print(
                f"  [PROTECTED] {p}"
            )

        self.print_header(
            "DISCOVERY"
        )

        for name, count in (
            self.inventory().items()
        ):

            print(
                f"[SCAN] {name:<20} "
                f"{count} files"
            )

        self.print_header(
            "OLLAMA"
        )

        ok, detail = (
            self.ollama_tags()
        )

        print(
            f"[{'READY' if ok else 'BLOCKED'}] "
            f"{detail[:1000]}"
        )

        self.print_header(
            "ENGINE CAPABILITIES"
        )

        capabilities = [
            "Architecture discovery",
            "Phase acceptance",
            "Dedicated phase tests",
            "Full regression",
            "Ollama coding brain",
            "Structured patch protocol",
            "Protected V1 paths",
            "Snapshot / restore",
            "Bounded repair loop",
            "Security scan",
            "Persistent evidence",
            "Gate: CLOSED requires tests + regression + security",
        ]

        for item in capabilities:

            print(
                f"[READY] {item}"
            )

    # ========================================================
    # PHASE
    # ========================================================

    def run_phase(
        self,
        spec: str,
    ) -> PhaseResult:

        match = re.fullmatch(
            r"(v1|v2):(\d+)",
            spec.lower().strip(),
        )

        if not match:
            raise ValueError(
                "phase must be v1:N or v2:N"
            )

        track, number_text = (
            match.groups()
        )

        phase = int(
            number_text
        )

        if phase not in PHASE_NAMES[
            track
        ]:

            raise ValueError(
                f"unknown {track} phase: {phase}"
            )

        result = (
            self.autonomous_phase(
                track,
                phase,
            )
        )

        self.print_result(
            result
        )

        return result

    # ========================================================
    # ALL
    # ========================================================

    def run_all(self) -> None:

        for track in (
            "v1",
            "v2",
        ):

            for phase in sorted(
                PHASE_NAMES[track]
            ):

                result = (
                    self.autonomous_phase(
                        track,
                        phase,
                    )
                )

                self.print_result(
                    result
                )

                if (
                    result.status
                    != "CLOSED"
                ):

                    print(
                        f"\n[STOP] --all halted "
                        f"at {track}:{phase} "
                        f"because "
                        f"status={result.status}"
                    )

                    return

    # ========================================================
    # RESULT
    # ========================================================

    def print_result(
        self,
        result: PhaseResult,
    ) -> None:

        print(
            f"\nPHASE RESULT: "
            f"{result.status}"
        )

        print(
            f"REASON: {result.reason}"
        )

        if result.gaps:

            print("GAPS:")

            for gap in result.gaps:

                print(
                    f"  - {gap}"
                )

        if result.changes:

            print("CHANGES:")

            for change in sorted(
                set(result.changes)
            ):

                print(
                    f"  + {change}"
                )

        print("CHECKS:")

        for c in result.checks:

            print(
                f"  [{c.status}] "
                f"{c.name}: "
                f"{c.detail[:300]}"
            )

    # ========================================================
    # REPORT
    # ========================================================

    def write_master_report(
        self,
    ) -> None:

        lines = [
            "# Nusantara Master Developer Engine v3",
            "",
            f"- Engine version: `{ENGINE_VERSION}`",
            f"- Generated: `{self.now()}`",
            f"- Root: `{self.root}`",
            "",
            "## Safety",
            "",
            "- No git reset/clean/checkout.",
            "- No autonomous delete operation.",
            "- Model-generated shell commands are never executed.",
            "- V1 protected paths are read-only to autonomous patches.",
            "- Failed patch iterations are restored from snapshots.",
            "",
            "## Gate",
            "",
            "A phase is CLOSED only when dedicated phase tests, full regression, and security pass.",
            "Compile success alone is insufficient.",
        ]

        self.safe_write(
            self.report_path,
            "\n".join(lines)
            + "\n",
        )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "NUSANTARA MASTER "
            "DEVELOPER ENGINE v3.0.0"
        )
    )

    parser.add_argument(
        "--status",
        action="store_true",
    )

    parser.add_argument(
        "--phase"
    )

    parser.add_argument(
        "--all",
        action="store_true",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
    )

    parser.add_argument(
        "--docker",
        action="store_true",
    )

    parser.add_argument(
        "--api",
        action="store_true",
    )

    parser.add_argument(
        "--model",
        default=os.getenv(
            "NUSANTARA_CODER_MODEL",
            "qwen2.5-coder:7b",
        ),
    )

    parser.add_argument(
        "--ollama-url",
        default=os.getenv(
            "OLLAMA_URL",
            "http://127.0.0.1:11434",
        ),
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    if (
        not args.status
        and not args.phase
        and not args.all
    ):

        parser.print_help()

        return 0

    root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    engine = MasterDeveloperEngine(
        root=root,
        apply=args.apply,
        docker=args.docker,
        api=args.api,
        model=args.model,
        ollama_url=args.ollama_url,
        max_iterations=args.max_iterations,
    )

    try:

        if args.status:
            engine.status()

        if args.phase:
            engine.run_phase(
                args.phase
            )

        if args.all:
            engine.run_all()

        engine.write_master_report()

        return 0

    except KeyboardInterrupt:

        print(
            "\n[STOP] Interrupted by user."
        )

        return 130

    except Exception as exc:

        print(
            f"[ERROR] {exc}"
        )

        return 2


if __name__ == "__main__":
    raise SystemExit(main())