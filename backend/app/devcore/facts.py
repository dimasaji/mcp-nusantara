"""Fakta statis terverifikasi dari source Python (AST) - dasar grounding & fallback tanpa LLM."""
from __future__ import annotations

import ast
from urllib.parse import urlparse

_HTTP_FUNCS = {"urlopen", "get", "post", "put", "delete", "request", "head", "patch"}
_LOCAL = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}


def static_facts(path: str, content: str) -> list[str]:
    lines = content.count("\n") + 1
    if not path.lower().endswith(".py"):
        return [f"Bukan file Python; {lines} baris."]
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return [f"Tidak dapat di-parse sebagai Python (SyntaxError baris {exc.lineno})."]
    imports, funcs, classes = [], [], []
    prints = opens = 0
    http, loops, tries = [], False, False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module or ".")
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(n.name)
        elif isinstance(n, ast.ClassDef):
            classes.append(n.name)
        elif isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
            loops = True
        elif isinstance(n, ast.Try):
            tries = True
        elif isinstance(n, ast.Call):
            fn = n.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name == "print":
                prints += 1
            elif name == "open":
                opens += 1
            elif name in _HTTP_FUNCS and n.args and isinstance(n.args[0], ast.Constant) \
                    and isinstance(n.args[0].value, str) and n.args[0].value.startswith(("http://", "https://")):
                url = n.args[0].value
                host = urlparse(url).hostname or "?"
                tmo = next((k.value.value for k in n.keywords if k.arg == "timeout" and isinstance(k.value, ast.Constant)), None)
                http.append(f"HTTP request ke {url} (host {'localhost' if host in _LOCAL else 'EKSTERNAL'}), "
                            f"timeout={tmo if tmo is not None else 'tidak diatur'}")
    f = [f"{lines} baris."]
    if imports:
        f.append("Import: " + ", ".join(dict.fromkeys(imports)))
    if funcs:
        f.append("Fungsi: " + ", ".join(dict.fromkeys(funcs)))
    if classes:
        f.append("Kelas: " + ", ".join(classes))
    f += http or ["Tidak ada panggilan HTTP dengan URL literal terlihat."]
    f.append(f"Panggilan print(): {prints}" if prints else "Tidak ada panggilan print().")
    f.append("Ada loop (for/while)." if loops else "Tidak ada loop terlihat (tidak ada retry).")
    f.append("Ada try/except." if tries else "Tidak ada try/except.")
    f.append(f"Panggilan open(): {opens}" if opens else "Tidak ada penulisan/penyimpanan file (open) terlihat.")
    return f
