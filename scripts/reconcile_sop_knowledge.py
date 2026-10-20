"""Rekonsiliasi read-only: 42 PDF SOP vs pipeline vs knowledge aktif yang dipakai Chat.

Tidak menulis ke basis pengetahuan mana pun; hanya membaca dan menghasilkan laporan.
"""
from __future__ import annotations
import hashlib, json, re, sqlite3, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "data/knowledge/sop"
ORIG = SOP / "original"
ENGINE_OUT = SOP / "engine_output"
STORE = ROOT / "data/knowledge/nusantara_knowledge.db"

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def text_layer_chars(p: Path):
    """(jumlah_halaman, total_karakter_text_layer, metode) atau (None,None,alasan)."""
    try:
        import fitz  # PyMuPDF
    except Exception:
        try:
            from pypdf import PdfReader
        except Exception:
            return None, None, "NO_PDF_LIBRARY"
        try:
            r = PdfReader(str(p))
            return len(r.pages), sum(len((pg.extract_text() or "")) for pg in r.pages), "pypdf"
        except Exception as exc:
            return None, None, f"pypdf:{type(exc).__name__}"
    try:
        doc = fitz.open(str(p))
        total = sum(len(pg.get_text("text") or "") for pg in doc)
        pages = doc.page_count
        doc.close()
        return pages, total, "pymupdf"
    except Exception as exc:
        return None, None, f"pymupdf:{type(exc).__name__}"

def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())

def main() -> int:
    pdfs = sorted(ORIG.glob("*.pdf"))
    rows = []
    by_hash = defaultdict(list)
    for p in pdfs:
        digest = sha256(p)
        by_hash[digest].append(p.name)
        pages, chars, method = text_layer_chars(p)
        rows.append({"file": p.name, "size": p.stat().st_size, "sha256": digest,
                     "pages": pages, "text_layer_chars": chars, "text_method": method})

    # pipeline output
    engine_dirs = {d.name for d in ENGINE_OUT.iterdir() if d.is_dir()} if ENGINE_OUT.exists() else set()
    # knowledge aktif -> referensi "Sumber: <file>, halaman N"
    stored = {}
    if STORE.exists():
        conn = sqlite3.connect(str(STORE)); conn.row_factory = sqlite3.Row
        docs = {r["document_id"]: r for r in conn.execute("select * from documents")}
        ref = defaultdict(set)
        chars_per_doc = defaultdict(int)
        chunks_per_doc = defaultdict(int)
        for r in conn.execute("select document_id, content from chunks"):
            chunks_per_doc[r["document_id"]] += 1
            chars_per_doc[r["document_id"]] += len(r["content"] or "")
            for m in re.finditer(r"Sumber:\s*([^,\n]+?\.pdf)[,\s]*halaman\s*(\d+)", r["content"] or "", re.I):
                ref[r["document_id"]].add((m.group(1).strip(), int(m.group(2))))
        for did, d in docs.items():
            stored[did] = {"title": d["title"], "chunks": chunks_per_doc.get(did, 0),
                           "chars": chars_per_doc.get(did, 0), "refs": sorted(ref.get(did, []))}
        conn.close()

    ref_to_doc = defaultdict(list)
    for did, info in stored.items():
        for f, page in info["refs"]:
            ref_to_doc[norm(f)].append((did, info["title"], page))

    for r in rows:
        key = norm(r["file"])
        eng = [d for d in engine_dirs if norm(d).startswith(key) or key.startswith(norm(d))]
        hit = ref_to_doc.get(key, [])
        r["in_pipeline"] = bool(eng)
        r["pipeline_dir"] = eng[0] if eng else None
        r["in_store"] = bool(hit)
        r["store_docs"] = sorted({h[0] for h in hit})
        r["store_pages"] = sorted({h[2] for h in hit})
        r["store_chars"] = sum(stored[did]["chars"] for did in {x[0] for x in hit}) if hit else 0
        if r["in_store"]:
            r["status"] = "READY_IN_CHAT" if r["store_chars"] >= 400 else "PARTIAL_THIN"
        elif r["in_pipeline"]:
            r["status"] = "EXTRACTED_NOT_INGESTED"
        elif r["pages"] and (r["text_layer_chars"] or 0) > 200:
            r["status"] = "TEXT_LAYER_NOT_INGESTED"
        else:
            r["status"] = "SCAN_NOT_PROCESSED"

    counts = Counter(r["status"] for r in rows)
    dupes = {h: names for h, names in by_hash.items() if len(names) > 1}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "original_dir": str(ORIG), "pdf_count": len(rows),
        "status_counts": dict(counts),
        "ready_in_chat": counts.get("READY_IN_CHAT", 0),
        "duplicates_by_hash": dupes,
        "pipeline_documents": sorted(engine_dirs),
        "store_documents": {k: v for k, v in stored.items()},
        "rows": rows,
    }
    out_json = ROOT / "reports" / "SOP-RECONCILIATION.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"PDF di original      : {len(rows)}")
    print(f"status               : {dict(counts)}")
    print(f"siap dipakai Chat    : {report['ready_in_chat']}/{len(rows)}")
    print(f"duplikat (sha256)    : {len(dupes)}")
    print(f"dokumen di pipeline  : {len(engine_dirs)} -> {sorted(engine_dirs)}")
    print(f"dokumen di knowledge : {len(stored)}")
    print()
    print(f"{'file':<56} {'pages':>5} {'text':>8} {'pipe':>5} {'store':>5}  status")
    for r in rows:
        print(f"{r['file']:<56} {str(r['pages']):>5} {str(r['text_layer_chars']):>8} "
              f"{'ya' if r['in_pipeline'] else '-':>5} {'ya' if r['in_store'] else '-':>5}  {r['status']}")
    print()
    print("laporan JSON:", out_json.relative_to(ROOT))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
