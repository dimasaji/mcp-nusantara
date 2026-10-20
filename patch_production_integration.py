from pathlib import Path
import shutil
from datetime import datetime
import py_compile

target = Path("developer_core_engine.py")

if not target.exists():
    raise SystemExit("developer_core_engine.py tidak ditemukan.")

text = target.read_text(encoding="utf-8")

# ============================================================
# BACKUP
# ============================================================

backup = target.with_name(
    f"developer_core_engine.before_prod_integration_{datetime.now():%Y%m%d_%H%M%S}.py"
)

shutil.copy2(target, backup)

print("Backup:", backup)

# ============================================================
# CARI PIPELINE CHAT / RAG CONTEXT
# ============================================================

markers = [
    "evidence = _knowledge.search_knowledge(",
    "evidence_text = _build_evidence_text(",
    "def rag_context(",
    "@app.get(\"/v1/rag/context\")",
    "@app.get('/v1/rag/context')",
]

for marker in markers:
    print(
        f"{marker} =>",
        marker in text
    )

# ============================================================
# INTEGRASI KE /v1/rag/context
# ============================================================

if "production_evidence = search_production_knowledge(" in text:
    print("Production RAG sudah terhubung di suatu lokasi.")
else:

    # Cari endpoint context berdasarkan route decorator
    route_markers = [
        '@app.get("/v1/rag/context")',
        "@app.get('/v1/rag/context')",
    ]

    route_pos = -1

    for marker in route_markers:
        pos = text.find(marker)
        if pos != -1:
            route_pos = pos
            break

    if route_pos == -1:
        raise SystemExit(
            "Endpoint /v1/rag/context tidak ditemukan."
        )

    # Cari fungsi setelah decorator
    func_pos = text.find("def ", route_pos)

    if func_pos == -1:
        raise SystemExit(
            "Fungsi endpoint /v1/rag/context tidak ditemukan."
        )

    # Cari body awal fungsi
    body_start = text.find("\n", func_pos)

    if body_start == -1:
        raise SystemExit(
            "Body endpoint tidak ditemukan."
        )

    injection = r'''

    # ========================================================
    # PRODUCTION KNOWLEDGE RAG
    # ========================================================
    # Mengambil evidence dari:
    # data/knowledge/production_knowledge.db
    #
    # Graph RAG dan Source RAG tetap berjalan.
    # Production RAG hanya ditambahkan sebagai evidence.
    # ========================================================

    production_evidence = search_production_knowledge(
        query=q,
        top_k=5,
    )

    production_evidence_text = (
        build_production_evidence_text(
            production_evidence
        )
    )

'''

    # Cari return pertama setelah fungsi
    # Kita tidak menyisipkan secara membabi buta ke semua return.
    # Lebih aman mencari assignment context/evidence yang umum.
    function_end_candidates = []

    for marker in [
        "\n@app.",
        "\nasync def ",
        "\ndef ",
    ]:
        pos = text.find(marker, body_start + 1)
        if pos != -1:
            function_end_candidates.append(pos)

    function_end = min(function_end_candidates) if function_end_candidates else len(text)

    function_text = text[func_pos:function_end]

    # Cari variable context yang biasa dipakai endpoint
    context_markers = [
        "context =",
        "context_text =",
        "combined =",
        "result =",
    ]

    inserted = False

    for marker in context_markers:
        pos = function_text.find(marker)

        if pos != -1:
            absolute = func_pos + pos

            line_end = text.find("\n", absolute)

            if line_end == -1:
                line_end = absolute + len(text[absolute:])

            text = (
                text[:line_end + 1]
                + injection
                + text[line_end + 1:]
            )

            inserted = True
            print(
                "Production RAG disisipkan setelah:",
                marker
            )
            break

    if not inserted:

        # Fallback:
        # sisipkan tepat setelah signature/body awal.
        text = (
            text[:body_start + 1]
            + injection
            + text[body_start + 1:]
        )

        print(
            "Production RAG disisipkan pada awal body endpoint."
        )

# ============================================================
# CHAT PIPELINE
# ============================================================

# Kita juga mencoba mengintegrasikan pipeline chat apabila
# _knowledge.search_knowledge memang ada.
#
# Hanya dilakukan bila belum ada integrasi sebelumnya.

if "production_evidence = search_production_knowledge(" not in text:

    chat_marker = "evidence = _knowledge.search_knowledge("

    chat_pos = text.find(chat_marker)

    if chat_pos != -1:

        line_end = text.find("\n", chat_pos)

        if line_end == -1:
            line_end = len(text)

        # Tentukan indentasi dari baris evidence
        line_start = text.rfind(
            "\n",
            0,
            chat_pos
        ) + 1

        line = text[line_start:chat_pos]

        indent = ""
        for char in line:
            if char in (" ", "\t"):
                indent += char
            else:
                break

        chat_injection = f'''
{indent}# Production Knowledge RAG
{indent}production_evidence = search_production_knowledge(
{indent}    query=request.user_input,
{indent}    top_k=settings.retrieval_top_k,
{indent})
{indent}
{indent}for production_item in production_evidence:
{indent}    if isinstance(evidence, list):
{indent}        evidence.append(production_item)
'''

        text = (
            text[:line_end + 1]
            + chat_injection
            + text[line_end + 1:]
        )

        print(
            "Production RAG ditambahkan ke chat pipeline."
        )

# ============================================================
# SIMPAN
# ============================================================

target.write_text(
    text,
    encoding="utf-8",
)

# ============================================================
# VALIDASI PYTHON
# ============================================================

try:

    py_compile.compile(
        str(target),
        doraise=True,
    )

    print()
    print("==============================================")
    print("SYNTAX: OK")
    print("Production RAG integration: PATCHED")
    print("==============================================")
    print()

except Exception as exc:

    print()
    print("SYNTAX ERROR")
    print(exc)
    print()
    print("Backup tersedia:")
    print(backup)

    # Restore otomatis jika syntax rusak
    shutil.copy2(
        backup,
        target,
    )

    print("File dikembalikan ke kondisi sebelum patch.")

    raise
