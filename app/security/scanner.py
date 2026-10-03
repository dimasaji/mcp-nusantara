"""Phase 20 - pemindai secret statis. Temuan tidak pernah menampilkan nilai secret."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

RULES = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "hardcoded_credential": re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
}
SKIP_DIRS = {".git", "__pycache__", "data", ".venv", "node_modules", ".mypy_cache", ".ruff_cache"}
EXTS = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json", ".env", ".example", ".sh", ".ps1", ".html", ".cfg", ".ini"}


@dataclass
class Finding:
    path: str
    line: int
    rule: str


def scan_tree(root: Path) -> list[Finding]:
    out: list[Finding] = []
    root = Path(root)
    for p in root.rglob("*"):
        if not p.is_file() or set(p.relative_to(root).parts) & SKIP_DIRS:
            continue
        if p.suffix not in EXTS and p.name not in {".env", ".env.example"}:
            continue
        try:
            lines = p.read_text("utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if "nosecret" in line:
                continue
            for name, rx in RULES.items():
                if rx.search(line):
                    out.append(Finding(str(p.relative_to(root)), i, name))
    return out
