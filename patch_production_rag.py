from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(r"C:\Users\dmaza\mcp-starter")
TARGET = ROOT / "developer_core_engine.py"

if not TARGET.exists():
    raise SystemExit("developer_core_engine.py tidak ditemukan.")

text = TARGET.read_text(encoding="utf-8")

backup = TARGET.with_name(
    f"developer_core_engine.before_production_rag_{datetime.now():%Y%m%d_%H%M%S}.py"
)
shutil.copy2(TARGET, backup)

print(f"Backup: {backup}")

# ============================================================
# 1. TAMBAHKAN IMPORT PRODUCTION HYBRID RAG
# ============================================================

marker = "from pydantic import BaseModel"

if "from app.knowledge.production_hybrid_rag import ProductionHybridRAG" not in text:
    if marker in text:
        text = text.replace(
            marker,
            marker
            + "\n\ntry:\n"
            + "    from app.knowledge.production_hybrid_rag import ProductionHybridRAG\n"
            + "except Exception:\n"
            + "    ProductionHybridRAG = None\n",
            1,
        )
    else:
        print("WARNING: marker import tidak ditemukan.")

# ============================================================
# 2. TAMBAHKAN PRODUCTION RAG INSTANCE
# ============================================================

instance_marker = "_file_hashes = {}"

if "_production_rag" not in text:
    if instance_marker in text:
        text = text.replace(
            instance_marker,
            instance_marker
            + "\n\n# Production Knowledge RAG\n"
            + "_production_rag = None\n",
            1,
        )
    else:
        print("WARNING: marker instance tidak ditemukan.")

# ============================================================
# 3. TAMBAHKAN HELPER PRODUCTION RAG
# ============================================================

helper_marker = "\ndef graph_summary():"

if "def search_production_knowledge(" not in text:

    helper = r'''

def get_production_rag():
    """
    Lazy loader untuk Production Hybrid RAG.

    Tidak membuat Production RAG wajib tersedia agar
    Developer Core tetap dapat berjalan apabila dependency
    semantic retrieval belum siap.
    """
    global _production_rag

    if ProductionHybridRAG is None:
        return None

    if _production_rag is None:
        try:
            _production_rag = ProductionHybridRAG()
        except Exception:
            _production_rag = None

    return _production_rag


def search_production_knowledge(
    query: str,
    top_k: int = 5,
    intent_name: str | None = None,
):
    """
    Mengambil evidence dari Production Hybrid RAG.

    Output dibuat menjadi dictionary sederhana agar aman
    digabungkan dengan Graph RAG dan Source RAG.
    """

    rag = get_production_rag()

    if rag is None:
        return []

    try:
        if not rag.database_exists():
            return []

        pack = rag.retrieve_for_intent(
            query=query,
            intent_name=intent_name,
            top_k=top_k,
        )

        results = []

        evidence_items = getattr(
            pack,
            "evidence",
            None,
        )

        if evidence_items is None:
            evidence_items = getattr(
                pack,
                "items",
                [],
            )

        for item in evidence_items or []:

            if isinstance(item, dict):
                data = item
            else:
                data = {
                    "chunk_id": getattr(
                        item,
                        "chunk_id",
                        None,
                    ),
                    "document_id": getattr(
                        item,
                        "document_id",
                        None,
                    ),
                    "text": getattr(
                        item,
                        "text",
                        None,
                    ),
                    "chunk": getattr(
                        item,
                        "text",
                        None,
                    ),
                    "score": getattr(
                        item,
                        "score",
                        None,
                    ),
                    "semantic_score": getattr(
                        item,
                        "semantic_score",
                        None,
                    ),
                    "lexical_score": getattr(
                        item,
                        "lexical_score",
                        None,
                    ),
                    "source": getattr(
                        item,
                        "source",
                        None,
                    ),
                    "title": getattr(
                        item,
                        "title",
                        None,
                    ),
                    "authority": getattr(
                        item,
                        "authority",
                        None,
                    ),
                    "url": getattr(
                        item,
                        "url",
                        None,
                    ),
                    "content_type": getattr(
                        item,
                        "content_type",
                        None,
                    ),
                    "service": getattr(
                        item,
                        "service",
                        None,
                    ),
                    "source_status": getattr(
                        item,
                        "source_status",
                        None,
                    ),
                }

            text_value = (
                data.get("text")
                or data.get("chunk")
                or data.get("content")
                or ""
            )

            if not str(text_value).strip():
                continue

            results.append(
                {
                    "type": "production_knowledge",
                    "chunk_id": data.get("chunk_id"),
                    "document_id": data.get("document_id"),
                    "title": data.get("title"),
                    "text": str(text_value).strip(),
                    "chunk": str(text_value).strip(),
                    "score": data.get("score"),
                    "semantic_score": data.get(
                        "semantic_score"
                    ),
                    "lexical_score": data.get(
                        "lexical_score"
                    ),
                    "source": data.get("source"),
                    "authority": data.get("authority"),
                    "url": data.get("url"),
                    "content_type": data.get(
                        "content_type"
                    ),
                    "service": data.get("service"),
                    "source_status": data.get(
                        "source_status"
                    ),
                }
            )

        return results

    except Exception as exc:

        print(
            "[Production RAG] retrieval failed:",
            exc,
        )

        return []


def build_production_evidence_text(
    results,
) -> str:

    if not results:
        return ""

    lines = []

    for index, item in enumerate(
        results,
        start=1,
    ):

        lines.append(
            f"[PRODUCTION KNOWLEDGE {index}]"
        )

        if item.get("title"):
            lines.append(
                f"Title: {item['title']}"
            )

        if item.get("service"):
            lines.append(
                f"Service: {item['service']}"
            )

        if item.get("content_type"):
            lines.append(
                f"Content Type: {item['content_type']}"
            )

        if item.get("source_status"):
            lines.append(
                f"Source Status: {item['source_status']}"
            )

        if item.get("authority") is not None:
            lines.append(
                f"Authority: {item['authority']}"
            )

        if item.get("source"):
            lines.append(
                f"Source: {item['source']}"
            )

        if item.get("score") is not None:
            lines.append(
                f"Score: {item['score']}"
            )

        lines.append(
            f"Text: {item.get('text', '')}"
        )

        lines.append("")

    return "\n".join(lines).strip()

'''

    if helper_marker in text:
        text = text.replace(
            helper_marker,
            helper + helper_marker,
            1,
        )
    else:
        print("WARNING: marker graph_summary tidak ditemukan.")

# ============================================================
# 4. PATCH CHAT: SETELAH KNOWLEDGE ENGINE
# ============================================================

old = '''        evidence = _knowledge.search_knowledge(
            request.user_input,
            top_k=settings.retrieval_top_k,
        )
'''

new = '''        evidence = _knowledge.search_knowledge(
            request.user_input,
            top_k=settings.retrieval_top_k,
        )

        # ----------------------------------------------------------
        # PRODUCTION KNOWLEDGE RAG
        # ----------------------------------------------------------
        # Evidence dari production_knowledge.db digabungkan
        # dengan evidence legacy tanpa mengubah Knowledge Engine.
        # ----------------------------------------------------------

        production_evidence = search_production_knowledge(
            query=request.user_input,
            top_k=settings.retrieval_top_k,
        )

        for item in production_evidence:
            evidence.append(
                item
            )
'''

if old in text and "production_evidence = search_production_knowledge(" not in text:
    text = text.replace(
        old,
        new,
        1,
    )
else:
    print("WARNING: blok Knowledge Engine tidak ditemukan atau sudah dipatch.")

# ============================================================
# 5. PATCH EVIDENCE TEXT AGAR DIKENALI HERMES
# ============================================================

old2 = '''        evidence_text = _build_evidence_text(
            evidence
        )
'''

new2 = '''        evidence_text = _build_evidence_text(
            evidence
        )

        production_evidence_text = (
            build_production_evidence_text(
                production_evidence
            )
        )

        if production_evidence_text:
            evidence_text = (
                evidence_text
                + "\\n\\n"
                + production_evidence_text
            )
'''

if old2 in text and "production_evidence_text = (" not in text:
    text = text.replace(
        old2,
        new2,
        1,
    )
else:
    print("WARNING: blok evidence_text tidak ditemukan atau sudah dipatch.")

# ============================================================
# 6. PATCH RESPONSE EVIDENCE
# ============================================================

old3 = '''                    "score": getattr(
                        e,
                        "score",
                        None,
                    ),
'''

new3 = '''                    "score": getattr(
                        e,
                        "score",
                        None,
                    ),
                    "type": (
                        e.get("type")
                        if isinstance(e, dict)
                        else None
                    ),
                    "chunk_id": (
                        e.get("chunk_id")
                        if isinstance(e, dict)
                        else None
                    ),
                    "semantic_score": (
                        e.get("semantic_score")
                        if isinstance(e, dict)
                        else None
                    ),
                    "lexical_score": (
                        e.get("lexical_score")
                        if isinstance(e, dict)
                        else None
                    ),
                    "authority": (
                        e.get("authority")
                        if isinstance(e, dict)
                        else None
                    ),
                    "service": (
                        e.get("service")
                        if isinstance(e, dict)
                        else None
                    ),
'''

if old3 in text and '"semantic_score": (' not in text:
    text = text.replace(
        old3,
        new3,
        1,
    )

# ============================================================
# 7. VALIDASI SYNTAX
# ============================================================

TARGET.write_text(
    text,
    encoding="utf-8",
)

print("Patch selesai.")

import py_compile

try:
    py_compile.compile(
        str(TARGET),
        doraise=True,
    )
    print("SYNTAX: OK")
except Exception as exc:
    print("SYNTAX: ERROR")
    print(exc)
    print("Backup masih tersedia:")
    print(backup)
    raise

print()
print("Production Hybrid RAG sekarang terhubung ke Developer Core.")
print("Restart Developer Core untuk memuat perubahan.")
