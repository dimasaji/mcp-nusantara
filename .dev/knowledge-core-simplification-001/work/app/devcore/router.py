"""Intent + generic file-reference extraction (workflow #7-#9). Tanpa hard-code nama file.
Teks asli SELALU dipertahankan (skill #9): normalized_text hanya merapikan spasi."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.devcore.workspace import is_sensitive_name
from app.devcore.inspection import inspection_preview

_EXT = "py|md|toml|json|ya?ml|txt|ini|cfg|env|html|css|js|ts|tsx|jsx|ps1|sh|bat|sql|csv|lock|example"
_FILE = re.compile(rf"(?<![\w/\\.:@-])((?:[A-Za-z]:[/\\]|/)?(?:[\w.\-]+[/\\])*[\w.\-]+\.(?:{_EXT}))(?![\w])", re.I)
_QUOTED = re.compile(rf"[\"'`]([^\"'`\n]+\.(?:{_EXT}))[\"'`]", re.I)
_DOTENV = re.compile(r"(?<![\w/\\.])(\.env(?:\.\w+)?)(?![\w])", re.I)
_DIR_WORD = re.compile(r"\b(?:folder|direktori|directory|dir|struktur(?:\s+proyek|\s+project)?)\s+[\"'`]?([\w.\-/\\]+)", re.I)
_DIR_SLASH = re.compile(r"(?<![\w/\\])((?:[\w.\-]+[/\\])+)(?=[\s,.;]|$)")
_FIND_NAME = re.compile(r"\b(?:cari|temukan|find|search)\s+(?:file\s+)?[\"'`]?([\w.\-*?]+)", re.I)
_STOP = {"ini", "itu", "tersebut", "yang", "ada", "di", "ke", "dan", "file", "folder", "proyek", "project", "saya", "kita"}

_READ = r"\b(baca|lihat|tampilkan|analisis|analisa|jelaskan|cek|buka|periksa|review|read|show|analyze|explain|open|isi file)\b"
_FIND = r"\b(cari|temukan|find|search|dimana|di mana|lokasi)\b"
_LIST = r"\b(daftar|list|struktur|tree|isi folder|isi direktori)\b"
_FOLDER = r"\b(folder|direktori|directory|dir|struktur)\b"
_MODIFY = (r"\b(ubah|edit|tulis|hapus|ganti|patch|perbaiki|tambah|tambahkan|buat file|install|jalankan|execute|"
           r"git push|delete|rename|pindahkan|modify|fix|write)\b")
VERBATIM = re.compile(r"\b(persis|apa adanya|tampilkan isi|isi file tersebut|isi lengkap|exact|verbatim)\b", re.I)


@dataclass
class DevPlan:
    handled: bool
    intent: str
    original_text: str
    normalized_text: str
    file_references: list[str] = field(default_factory=list)
    actions: list[tuple[str, str]] = field(default_factory=list)   # (mode, target)
    modify_requested: bool = False
    verbatim: bool = False
    inspection: dict | None = None


def extract_file_refs(text: str) -> list[str]:
    seen: list[str] = []
    for rx in (_QUOTED, _FILE, _DOTENV):
        for m in rx.finditer(text):
            ref = m.group(1).strip().replace("\\", "/")
            if ref and ref not in seen and not any(ref != s and ref in s for s in seen):
                seen.append(ref)
    return seen


def plan(text: str, max_files: int = 3) -> DevPlan:
    orig = text
    norm = re.sub(r"\s+", " ", text).strip()
    low = norm.lower()
    refs = extract_file_refs(norm)[:max_files]
    has = lambda pat: re.search(pat, low) is not None  # noqa: E731
    read_v, find_v, modify_v = has(_READ), has(_FIND), has(_MODIFY)
    folder_ctx = has(_FOLDER) or _DIR_SLASH.search(norm) is not None
    list_v = has(_LIST) and folder_ctx
    preview = inspection_preview(orig, explicit_source=bool(refs) or list_v or bool(
        re.search(r'\b(?:cari|temukan|find|search)\s+file\b', low)))
    if preview is not None:
        return DevPlan(True, 'inspection_preview', orig, norm, modify_requested=modify_v,
                       inspection=preview)
    actions: list[tuple[str, str]] = []
    if refs:
        for r in refs:
            bare = "/" not in r and not is_sensitive_name(r)  # file sensitif: baca langsung agar DIBLOKIR eksplisit
            if find_v and not read_v and bare:
                actions.append(("find", r))
            elif bare:
                actions.append(("find_then_read", r))
            else:
                actions.append(("read", r))
        intent = "find_file" if all(m == "find" for m, _ in actions) else "read_file"
    elif find_v and (m := _FIND_NAME.search(norm)) and m.group(1).lower() not in _STOP:
        actions.append(("find", m.group(1)))
        intent = "find_file"
    elif list_v:
        d = _DIR_SLASH.search(norm) or _DIR_WORD.search(norm)
        target = d.group(1).rstrip("/\\") if d and d.group(1).lower() not in _STOP else "."
        actions.append(("list", target or "."))
        intent = "list_directory"
    else:
        return DevPlan(False, "none", orig, norm)
    return DevPlan(True, intent, orig, norm, refs, actions, modify_v, bool(VERBATIM.search(norm)))
