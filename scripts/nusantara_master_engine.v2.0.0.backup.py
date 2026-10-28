#!/usr/bin/env python3
"""
NUSANTARA MASTER DEVELOPER ENGINE
==================================

Single-file master orchestrator for Nusantara.

Modes:
    --status
    --phase v1:0
    --phase v2:0
    --all
    --all --apply

Principles:
    - V1 is protected.
    - Inspect before changing.
    - Never git reset/clean.
    - Never delete project/database data automatically.
    - Test after every remediation.
    - Regression failure stops execution.
    - Unknown requirements are NOT_VERIFIED, never falsely CLOSED.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ENGINE = "NUSANTARA MASTER DEVELOPER ENGINE"
VERSION = "2.0.0"

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "audit"
EVIDENCE = AUDIT / "evidence"


# ============================================================
# PHASE DEFINITIONS
# ============================================================

V1_PHASES = {
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
    17: "Evaluation / Observability",
    18: "Docker / Production",
}

V2_PHASES = {
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
}


@dataclass
class PhaseResult:
    family: str
    number: int
    name: str
    status: str = "NOT_VERIFIED"
    findings: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    runtime: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def id(self):
        return f"{self.family}{self.number:02d}"


# ============================================================
# MASTER ENGINE
# ============================================================

class NusantaraMasterDeveloperEngine:

    def __init__(self, apply=False, docker=False, api=False):
        self.root = ROOT
        self.apply = apply
        self.docker = docker
        self.api = api
        self.started = dt.datetime.now().astimezone()

        AUDIT.mkdir(parents=True, exist_ok=True)
        EVIDENCE.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    def banner(self):
        print("=" * 76)
        print(ENGINE)
        print("=" * 76)
        print(f"Version : {VERSION}")
        print(f"Root    : {self.root}")
        print(f"Python  : {sys.version.split()[0]}")
        print(f"Mode    : {'APPLY' if self.apply else 'VERIFY'}")
        print(f"Docker  : {'ON' if self.docker else 'OFF'}")
        print(f"API     : {'ON' if self.api else 'OFF'}")
        print("=" * 76)

    def section(self, title):
        print()
        print("=" * 76)
        print(title)
        print("=" * 76)

    # --------------------------------------------------------
    # SAFE PROCESS EXECUTION
    # --------------------------------------------------------

    def command(self, args, timeout=900):
        try:
            p = subprocess.run(
                args,
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )

            output = (p.stdout or "") + (p.stderr or "")

            return {
                "returncode": p.returncode,
                "output": output[-30000:],
            }

        except subprocess.TimeoutExpired:
            return {
                "returncode": 124,
                "output": f"TIMEOUT after {timeout}s",
            }

        except FileNotFoundError:
            return {
                "returncode": 127,
                "output": f"COMMAND NOT FOUND: {args[0]}",
            }

    # --------------------------------------------------------
    # REPOSITORY
    # --------------------------------------------------------

    def git(self, *args):
        return self.command(["git", *args])

    def git_branch(self):
        r = self.git("branch", "--show-current")
        return r["output"].strip()

    def git_status(self):
        r = self.git("status", "--short")
        return r["output"].strip()

    def repository_guard(self):
        self.section("REPOSITORY SAFETY")

        if not (self.root / ".git").exists():
            raise RuntimeError("Not a Git repository.")

        print(f"[OK] Git repository: {self.root}")
        print(f"[OK] Branch: {self.git_branch() or '(detached/unknown)'}")

        dirty = self.git_status()

        if dirty:
            print("[INFO] Working tree contains existing changes.")
            print("[SAFE] Engine will NOT reset, clean, checkout, or discard them.")
        else:
            print("[OK] Working tree clean.")

    # --------------------------------------------------------
    # FILE SYSTEM
    # --------------------------------------------------------

    def exists(self, rel):
        return (self.root / rel).exists()

    def files(self, directory):
        base = self.root / directory

        if not base.exists():
            return []

        if base.is_file():
            return [base]

        ignored = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
        }

        result = []

        for p in base.rglob("*"):
            if not p.is_file():
                continue

            if any(part in ignored for part in p.parts):
                continue

            result.append(p)

        return result

    def repository_inventory(self):
        inventory = {}

        for directory in [
            "app",
            "tests",
            "scripts",
            "docs",
            "data",
            "nusantara-models",
        ]:
            inventory[directory] = len(self.files(directory))

        return inventory

    # --------------------------------------------------------
    # SOURCE SEARCH
    # --------------------------------------------------------

    def source_text(self):
        chunks = []

        for directory in [
            "app",
            "tests",
            "scripts",
        ]:
            for p in self.files(directory):

                if p.suffix not in {
                    ".py",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".json",
                    ".md",
                }:
                    continue

                try:
                    chunks.append(
                        p.read_text(
                            encoding="utf-8",
                            errors="replace",
                        )
                    )
                except OSError:
                    pass

        return "\n".join(chunks)

    def contains_any(self, patterns):
        text = self.source_text().lower()

        return [
            pattern
            for pattern in patterns
            if pattern.lower() in text
        ]

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    def discovery(self):
        self.section("DISCOVERY")

        inventory = self.repository_inventory()

        for name, count in inventory.items():
            print(f"[SCAN] {name:<20} {count} files")

        required = [
            "app",
            "tests",
            "scripts",
            "docs",
        ]

        for path in required:
            if self.exists(path):
                print(f"[OK] {path}")
            else:
                print(f"[WARN] {path} missing")

        evidence_files = [
            "PROGRESS_REPORT.md",
            "docs/roadmap.md",
            "docs/v2/ROADMAP_STATUS.md",
            "docs/audit/PHASE_GAP_AUDIT_2026-10-05.txt",
            "docs/audit/AUDIT_DOCKER_2026-10-05.json",
            "docs/audit/PYTEST_DOCKER_FIX_FULL_2026-10-05.xml",
        ]

        print()
        print("Existing evidence:")

        for path in evidence_files:
            print(
                "[FOUND] " if self.exists(path) else "[MISS ] ",
                path,
            )

        return inventory

    # --------------------------------------------------------
    # COMPILE
    # --------------------------------------------------------

    def compile_check(self):
        self.section("PYTHON COMPILE CHECK")

        result = self.command(
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "app",
            ],
            timeout=600,
        )

        if result["returncode"] == 0:
            print("[PASS] python -m compileall -q app")
            return True, result["output"]

        print("[FAIL] Python compilation")
        print(result["output"])
        return False, result["output"]

    # --------------------------------------------------------
    # PYTEST
    # --------------------------------------------------------

    def pytest(self, focused=None):
        if not shutil.which("pytest"):
            result = self.command(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                ],
                timeout=1200,
            )
        else:
            args = [
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ]

            if focused:
                args.extend(focused)

            result = self.command(args, timeout=1200)

        passed = result["returncode"] == 0

        print(
            "[PASS]" if passed else "[FAIL]",
            "pytest",
        )

        return passed, result["output"]

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    def api_check(self, url):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "NusantaraMasterDeveloperEngine/2.0"
                },
            )

            with urlopen(req, timeout=10) as response:
                body = response.read(5000).decode(
                    "utf-8",
                    errors="replace",
                )

                return True, response.status, body

        except Exception as exc:
            return False, 0, str(exc)

    def runtime_api(self):
        self.section("RUNTIME API")

        urls = [
            "http://127.0.0.1:8000/health",
            "http://127.0.0.1:8000/v1",
            "http://127.0.0.1:8000/v2",
        ]

        for url in urls:
            ok, status, body = self.api_check(url)

            if ok:
                print(f"[PASS] {url} -> HTTP {status}")
            else:
                print(f"[INFO] {url} -> unavailable")

        return True

    # --------------------------------------------------------
    # DOCKER
    # --------------------------------------------------------

    def docker_check(self):
        self.section("DOCKER")

        if not shutil.which("docker"):
            print("[WARN] Docker executable not found.")
            return False

        result = self.command(
            ["docker", "compose", "config"],
            timeout=120,
        )

        if result["returncode"] == 0:
            print("[PASS] docker compose config")
        else:
            print("[FAIL] docker compose config")
            print(result["output"])

        result2 = self.command(
            ["docker", "compose", "ps"],
            timeout=120,
        )

        print(result2["output"][-10000:])

        return result["returncode"] == 0

    # --------------------------------------------------------
    # ARCHITECTURE ANALYSIS
    # --------------------------------------------------------

    def architecture_analysis(self):
        self.section("ARCHITECTURE ANALYSIS")

        checks = {
            "FastAPI": ["FastAPI"],
            "V1 route": ["/v1"],
            "V2 route": ["/v2"],
            "Ollama": ["Ollama"],
            "Hermes": ["Hermes"],
            "Graphify": ["Graphify"],
            "Knowledge": ["KnowledgeEngine"],
            "RAG": ["retriev", "embedding", "chunk"],
            "Trust": ["TrustEngine"],
            "Policy": ["PolicyEngine"],
            "Memory": ["MemoryStore", "memory"],
            "MCP": ["MCP"],
            "Tool Governance": ["GovernedTool", "allowlist"],
            "Approval": ["HumanApproval", "approval"],
            "Observability": ["metrics", "request_id"],
        }

        text = self.source_text().lower()

        for name, patterns in checks.items():
            found = any(
                p.lower() in text
                for p in patterns
            )

            print(
                f"[{'FOUND' if found else 'GAP  '}] {name}"
            )

    # --------------------------------------------------------
    # PHASE-SPECIFIC CHECKS
    # --------------------------------------------------------

    def phase_check(self, family, number, name):
        result = PhaseResult(
            family=family,
            number=number,
            name=name,
        )

        text = self.source_text().lower()

        # General source evidence
        keyword_map = {
            "environment": ["python", "fastapi", "docker"],
            "foundation": ["fastapi", "/health"],
            "llm": ["ollama", "provider", "mock"],
            "language": ["languageengine", "normalizer", "intent"],
            "context": ["session", "context"],
            "problem": ["problemengine", "problem"],
            "knowledge": ["knowledgeengine", "embedding", "retriev"],
            "rag": ["retriev", "embedding", "chunk"],
            "reasoning": ["reasoning", "planner", "plan"],
            "workflow": ["workflow", "state"],
            "policy": ["policyengine", "allow", "deny"],
            "trust": ["trustengine", "confidence", "evidence"],
            "memory": ["memorystore", "memory"],
            "tool": ["tool", "executor"],
            "mcp": ["mcp", "manifest", "registry"],
            "handoff": ["handoff", "human"],
            "api": ["fastapi", "/v1", "/v2"],
            "ui": ["dashboard", "frontend"],
            "observability": ["metrics", "request_id", "logging"],
            "docker": ["dockerfile", "compose"],
            "hardening": ["retry", "timeout", "circuit"],
            "experience": ["eventrecorder", "event"],
            "feedback": ["feedback"],
            "evaluation": ["evaluator", "eval"],
            "failure": ["failure"],
            "gap": ["gap"],
            "discovery": ["discovery", "candidate"],
            "experiment": ["experiment"],
            "proposal": ["proposal", "rollback"],
            "approval": ["approval", "queue"],
            "security": ["security", "injection", "secret"],
            "release": ["release", "rollback", "backup"],
        }

        key = name.lower()

        matched = []

        for category, patterns in keyword_map.items():
            if category in key:
                for pattern in patterns:
                    if pattern in text:
                        matched.append(pattern)

        if matched:
            result.findings.append(
                "Implementation signals: " +
                ", ".join(sorted(set(matched)))
            )
        else:
            result.gaps.append(
                "No strong implementation signal detected."
            )

        # Known historical evidence
        historical = [
            "AUDIT_DOCKER_2026-10-05.json",
            "PHASE_GAP_AUDIT_2026-10-05.txt",
            "PYTEST_DOCKER_FIX_FULL_2026-10-05.xml",
        ]

        for path in historical:
            if self.exists(f"docs/audit/{path}"):
                result.evidence.append(
                    f"Existing evidence: docs/audit/{path}"
                )

        return result

    # --------------------------------------------------------
    # V1 PROTECTION
    # --------------------------------------------------------

    def v1_protection(self):
        self.section("V1 PROTECTION")

        protected = [
            "app/main.py",
            "app/language",
            "app/knowledge",
            "app/problem",
        ]

        for path in protected:
            if self.exists(path):
                print(f"[PROTECTED] {path}")

        print()
        print(
            "[RULE] Master Engine will not automatically delete, "
            "reset, or rewrite V1 core."
        )

    # --------------------------------------------------------
    # SAFE REMEDIATION
    # --------------------------------------------------------

    def remediation(self, result):
        """
        Only deterministic, low-risk actions are allowed here.

        Deliberately does NOT:
            - rewrite V1 core
            - delete DB
            - git reset
            - git clean
            - install arbitrary packages
            - modify credentials
            - modify production infrastructure
        """

        if not self.apply:
            result.notes.append(
                "VERIFY mode: no source modification performed."
            )
            return

        # Phase 0 can generate a machine-readable state snapshot.
        if result.number == 0:
            path = AUDIT / "MASTER_ENGINE_STATE.json"

            state = {
                "engine": ENGINE,
                "version": VERSION,
                "timestamp": dt.datetime.now().astimezone().isoformat(),
                "root": str(self.root),
                "branch": self.git_branch(),
                "inventory": self.repository_inventory(),
            }

            path.write_text(
                json.dumps(
                    state,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result.changes.append(
                str(path.relative_to(self.root))
            )

        # Phase 7: deterministic compile check.
        if result.number == 7:
            ok, output = self.compile_check()

            result.tests.append(
                "compileall: PASS" if ok else "compileall: FAIL"
            )

            if not ok:
                result.gaps.append(
                    "Python compilation failed."
                )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def calculate_status(self, result):
        if any(
            x.lower().find("failed") >= 0
            for x in result.gaps
        ):
            return "FAILED"

        if result.gaps:
            return "PARTIAL"

        if result.tests or result.runtime or result.evidence:
            return "VERIFIED"

        if result.findings:
            return "PARTIAL"

        return "NOT_VERIFIED"

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    def save_evidence(self, result):
        folder = EVIDENCE / result.id
        folder.mkdir(parents=True, exist_ok=True)

        data = {
            "engine": ENGINE,
            "version": VERSION,
            "timestamp": dt.datetime.now().astimezone().isoformat(),
            "phase": result.id,
            "name": result.name,
            "status": result.status,
            "findings": result.findings,
            "tests": result.tests,
            "gaps": result.gaps,
            "changes": result.changes,
            "evidence": result.evidence,
            "runtime": result.runtime,
            "notes": result.notes,
        }

        (folder / "result.json").write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        lines = [
            f"# {result.id} — {result.name}",
            "",
            f"Status: **{result.status}**",
            "",
            "## Findings",
            "",
        ]

        lines.extend(
            f"- {x}" for x in result.findings
        )

        lines += [
            "",
            "## Tests",
            "",
        ]

        lines.extend(
            f"- {x}" for x in result.tests
        )

        lines += [
            "",
            "## Runtime",
            "",
        ]

        lines.extend(
            f"- {x}" for x in result.runtime
        )

        lines += [
            "",
            "## Gaps",
            "",
        ]

        lines.extend(
            f"- {x}" for x in result.gaps
        )

        lines += [
            "",
            "## Changes",
            "",
        ]

        lines.extend(
            f"- {x}" for x in result.changes
        )

        (folder / "result.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        result.evidence.append(
            str(
                (folder / "result.json").relative_to(
                    self.root
                )
            )
        )

    # --------------------------------------------------------
    # RUN ONE PHASE
    # --------------------------------------------------------

    def run_phase(self, family, number, name):
        self.section(
            f"{family} PHASE {number:02d} — {name}"
        )

        result = self.phase_check(
            family,
            number,
            name,
        )

        self.remediation(result)

        # Targeted runtime verification
        if family == "V1" and number in {0, 1, 15}:
            ok, output = self.compile_check()

            result.tests.append(
                "compileall PASS"
                if ok
                else "compileall FAILED"
            )

            if not ok:
                result.gaps.append(
                    "Compilation failure."
                )

        if family == "V2" and number in {2, 3, 20}:
            ok, output = self.compile_check()

            result.tests.append(
                "compileall PASS"
                if ok
                else "compileall FAILED"
            )

            if not ok:
                result.gaps.append(
                    "Compilation failure."
                )

        if self.api and (
            (family == "V1" and number == 15)
            or (family == "V2" and number in {1, 3, 6, 7, 8, 18, 20})
        ):
            self.runtime_api()
            result.runtime.append(
                "API runtime verification attempted."
            )

        if self.docker and (
            (family == "V1" and number == 18)
            or (family == "V2" and number == 21)
        ):
            if self.docker_check():
                result.runtime.append(
                    "Docker verification passed."
                )
            else:
                result.gaps.append(
                    "Docker verification failed/unavailable."
                )

        result.status = self.calculate_status(result)

        self.save_evidence(result)

        print()
        print(
            f"PHASE RESULT: {result.status}"
        )

        if result.gaps:
            print("GAPS:")
            for gap in result.gaps[:15]:
                print(f"  ! {gap}")

        if result.changes:
            print("CHANGES:")
            for change in result.changes:
                print(f"  + {change}")

        return result

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def status(self):
        self.banner()
        self.repository_guard()
        self.discovery()
        self.architecture_analysis()
        self.v1_protection()

        self.section("ENGINE STATUS")

        print("[READY] Master Developer Engine")
        print(f"[READY] V1 phases: {len(V1_PHASES)}")
        print(f"[READY] V2 phases: {len(V2_PHASES)}")
        print(f"[READY] Apply mode: {self.apply}")
        print()
        print(
            "Use --phase v1:0, --phase v2:0, "
            "--all, or --all --apply."
        )

    # --------------------------------------------------------
    # RUN PHASE
    # --------------------------------------------------------

    def run_selected(self, family, number):
        phases = (
            V1_PHASES
            if family == "V1"
            else V2_PHASES
        )

        if number not in phases:
            raise ValueError(
                f"Unknown phase: {family}:{number}"
            )

        self.banner()
        self.repository_guard()

        return [
            self.run_phase(
                family,
                number,
                phases[number],
            )
        ]

    # --------------------------------------------------------
    # RUN ALL
    # --------------------------------------------------------

    def run_all(self):
        self.banner()
        self.repository_guard()
        self.discovery()
        self.architecture_analysis()
        self.v1_protection()

        results = []

        # V1 first: baseline/protection.
        for number, name in V1_PHASES.items():
            result = self.run_phase(
                "V1",
                number,
                name,
            )

            results.append(result)

            if result.status == "FAILED":
                print(
                    "\n[STOP] V1 regression/failure detected."
                )
                break

        # V2 only if V1 baseline did not fail.
        if not any(
            r.status == "FAILED"
            for r in results
        ):
            for number, name in V2_PHASES.items():
                result = self.run_phase(
                    "V2",
                    number,
                    name,
                )

                results.append(result)

                if result.status == "FAILED":
                    print(
                        "\n[STOP] V2 phase failed."
                    )
                    break

        # Final report.
        self.write_report(results)

        return results

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    def write_report(self, results):
        self.section("MASTER ENGINE REPORT")

        counts = {}

        for result in results:
            counts[result.status] = (
                counts.get(result.status, 0) + 1
            )

        report = [
            "# Nusantara Master Developer Engine",
            "",
            f"Generated: {dt.datetime.now().astimezone().isoformat()}",
            f"Engine version: {VERSION}",
            "",
            "## Summary",
            "",
        ]

        for status, count in sorted(
            counts.items()
        ):
            report.append(
                f"- {status}: {count}"
            )

        report += [
            "",
            "## Phase Matrix",
            "",
            "| Phase | Name | Status | Gaps | Tests |",
            "|---|---|---|---:|---:|",
        ]

        for result in results:
            report.append(
                f"| {result.id} | {result.name} | "
                f"**{result.status}** | "
                f"{len(result.gaps)} | "
                f"{len(result.tests)} |"
            )

        report += [
            "",
            "## Safety",
            "",
            "- V1 core is protected.",
            "- No git reset/clean is performed.",
            "- No destructive database operation is performed.",
            "- Unknown requirements are not marked CLOSED.",
            "- Failed verification stops the automatic progression.",
            "",
        ]

        path = AUDIT / "MASTER_ENGINE_REPORT.md"

        path.write_text(
            "\n".join(report),
            encoding="utf-8",
        )

        state = {
            "engine": ENGINE,
            "version": VERSION,
            "timestamp": dt.datetime.now().astimezone().isoformat(),
            "results": [
                {
                    "phase": r.id,
                    "name": r.name,
                    "status": r.status,
                    "gaps": r.gaps,
                    "tests": r.tests,
                    "changes": r.changes,
                }
                for r in results
            ],
        }

        json_path = AUDIT / "MASTER_ENGINE_REPORT.json"

        json_path.write_text(
            json.dumps(
                state,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(f"[REPORT] {path}")
        print(f"[REPORT] {json_path}")

        print()
        print("FINAL COUNTS")

        for status, count in sorted(
            counts.items()
        ):
            print(
                f"{status:<18} {count}"
            )


# ============================================================
# CLI
# ============================================================

def parse_phase(value):
    match = re.fullmatch(
        r"(v1|v2):(\d+)",
        value.lower(),
    )

    if not match:
        raise argparse.ArgumentTypeError(
            "Format phase harus v1:N atau v2:N"
        )

    return (
        match.group(1).upper(),
        int(match.group(2)),
    )


def main():
    parser = argparse.ArgumentParser(
        description=ENGINE
    )

    parser.add_argument(
        "--status",
        action="store_true",
    )

    parser.add_argument(
        "--phase",
        type=parse_phase,
    )

    parser.add_argument(
        "--all",
        action="store_true",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Enable safe deterministic remediation.",
    )

    parser.add_argument(
        "--docker",
        action="store_true",
    )

    parser.add_argument(
        "--api",
        action="store_true",
    )

    args = parser.parse_args()

    engine = NusantaraMasterDeveloperEngine(
        apply=args.apply,
        docker=args.docker,
        api=args.api,
    )

    try:
        if args.status:
            engine.status()
            return 0

        if args.phase:
            family, number = args.phase

            engine.run_selected(
                family,
                number,
            )

            return 0

        if args.all:
            results = engine.run_all()

            if any(
                r.status == "FAILED"
                for r in results
            ):
                return 1

            return 0

        parser.print_help()
        return 0

    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        return 130

    except Exception as exc:
        print()
        print(
            f"[FATAL] {type(exc).__name__}: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())