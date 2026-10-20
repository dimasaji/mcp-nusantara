from pathlib import Path
from datetime import datetime
import shutil
import re

root = Path(r"C:\Users\dmaza\mcp-starter")
src = root / "nusantara_master_engine.py"

if not src.exists():
    raise SystemExit("ERROR: nusantara_master_engine.py tidak ditemukan.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"nusantara_master_engine_BACKUP_{stamp}.py"

shutil.copy2(src, backup)

text = src.read_text(encoding="utf-8-sig")

print("=" * 72)
print(" NUSANTARA MASTER ENGINE - MASTER INTEGRATION PATCH")
print("=" * 72)
print(f"Source : {src}")
print(f"Backup : {backup}")
print()


# ================================================================
# 1. DEVELOPER CORE CLIENT
# ================================================================

marker = "\n# ================================================================\n# OFFICIAL PRODUCTION KNOWLEDGE ENGINE\n# ================================================================\n"

if "class DeveloperCoreClient:" not in text:

    block = r'''
# ================================================================
# DEVELOPER CORE CLIENT
# ================================================================

class DeveloperCoreClient:

    """
    Adapter Master Engine -> Developer Core 8010.

    Developer Core tetap menjadi specialist engine:
      - Graph RAG
      - Source RAG
      - Graphify
      - source search
      - code analysis

    Master Engine hanya melakukan orchestration.
    """

    def __init__(
        self,
        base_url: str = DEVELOPER_CORE_URL,
    ):
        self.base_url = base_url.rstrip("/")

    def _get(
        self,
        path: str,
        timeout: int = 20,
    ) -> dict:

        url = self.base_url + path

        try:

            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "Accept": "application/json"
                },
            )

            with urllib.request.urlopen(
                req,
                timeout=timeout,
            ) as response:

                raw = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

                return json.loads(raw)

        except Exception as e:

            return {
                "status": "error",
                "error": str(e),
                "url": url,
            }

    def health(self) -> dict:

        result = self._get(
            "/v1/developer/health",
            timeout=5,
        )

        if result.get("status") != "error":
            return result

        return self._get(
            "/v1/health",
            timeout=5,
        )

    def rag_context(
        self,
        query: str,
        top_k: int = 8,
    ) -> dict:

        encoded = urllib.parse.quote(
            query,
            safe="",
        )

        result = self._get(
            f"/v1/rag/context?q={encoded}",
            timeout=30,
        )

        if result.get("status") == "error":

            return {
                "status": "error",
                "query": query,
                "items": [],
                "error": result.get(
                    "error"
                ),
            }

        return {
            "status": "ok",
            "query": query,
            "raw": result,
            "items": self._normalize_items(
                result,
                top_k,
            ),
        }

    def _normalize_items(
        self,
        data: dict,
        top_k: int = 8,
    ) -> list[dict]:

        items = []

        def add_items(
            values,
            source_type,
        ):

            if not isinstance(
                values,
                list,
            ):
                return

            for item in values:

                if isinstance(
                    item,
                    str,
                ):

                    items.append(
                        {
                            "source_type":
                                source_type,
                            "text": item,
                        }
                    )

                elif isinstance(
                    item,
                    dict,
                ):

                    copy = dict(item)

                    copy.setdefault(
                        "source_type",
                        source_type,
                    )

                    text = (
                        copy.get("text")
                        or copy.get("content")
                        or copy.get("snippet")
                        or copy.get("source")
                        or ""
                    )

                    copy["text"] = str(
                        text
                    )

                    items.append(copy)

        # Common Developer Core formats.

        add_items(
            data.get("graph"),
            "graph",
        )

        add_items(
            data.get("graph_results"),
            "graph",
        )

        add_items(
            data.get("source"),
            "source",
        )

        add_items(
            data.get("source_results"),
            "source",
        )

        add_items(
            data.get("evidence"),
            "evidence",
        )

        add_items(
            data.get("results"),
            "rag",
        )

        # Some versions return nested objects.

        for key in (
            "data",
            "context",
            "rag",
        ):

            nested = data.get(key)

            if isinstance(
                nested,
                dict,
            ):

                add_items(
                    nested.get("graph"),
                    "graph",
                )

                add_items(
                    nested.get("graph_results"),
                    "graph",
                )

                add_items(
                    nested.get("source"),
                    "source",
                )

                add_items(
                    nested.get("source_results"),
                    "source",
                )

                add_items(
                    nested.get("evidence"),
                    "evidence",
                )

                add_items(
                    nested.get("results"),
                    "rag",
                )

        return items[:top_k]

    def search(
        self,
        query: str,
        top_k: int = 8,
    ) -> dict:

        return self.rag_context(
            query,
            top_k,
        )


# ================================================================
# MASTER QUERY DOMAIN
# ================================================================

class MasterDomainEngine:

    SERVICE_TERMS = [
        "ktp",
        "ktp-el",
        "ktpel",
        "kartu tanda penduduk",
        "kartu keluarga",
        "kk",
        "kia",
        "akta kelahiran",
        "akta kematian",
        "kematian",
        "kelahiran",
        "perkawinan",
        "pernikahan",
        "perceraian",
        "cerai",
        "pindah",
        "domisili",
        "nik",
        "dukcapil",
        "dokumen kependudukan",
        "administrasi kependudukan",
        "pelayanan",
        "persyaratan",
        "syarat",
        "pengajuan",
        "permohonan",
        "status pengajuan",
        "berapa hari",
        "lama proses",
    ]

    DEVELOPER_TERMS = [
        "python",
        "powershell",
        "source code",
        "kode",
        "coding",
        "program",
        "programming",
        "developer",
        "engine",
        "api",
        "endpoint",
        "fastapi",
        "ollama",
        "graphify",
        "graph rag",
        "source rag",
        "rag",
        "database",
        "sqlite",
        "json",
        "bug",
        "error",
        "exception",
        "traceback",
        "function",
        "class",
        "module",
        "route",
        "routes.py",
        "developer_core_engine.py",
        "dependency",
        "dependencies",
        "powershell",
        "server",
        "uvicorn",
        "localhost",
        "port 8010",
        "port 8020",
    ]

    def classify(
        self,
        query: str,
    ) -> str:

        text = normalize_text(query)

        developer_score = sum(
            1
            for term in self.DEVELOPER_TERMS
            if term in text
        )

        service_score = sum(
            1
            for term in self.SERVICE_TERMS
            if term in text
        )

        if developer_score > 0:
            return "developer"

        if service_score > 0:
            return "service"

        return "general"

'''

    if marker not in text:
        raise SystemExit(
            "ERROR: marker Official Knowledge tidak ditemukan."
        )

    text = text.replace(
        marker,
        "\n" + block + marker,
        1,
    )

    print("[PASS] DeveloperCoreClient + MasterDomainEngine ditambahkan.")

else:

    print("[INFO] DeveloperCoreClient sudah ada. Tidak ditambahkan ulang.")


# ================================================================
# 2. FIX IMPORT urllib.parse
# ================================================================

if "import urllib.parse" not in text:

    text = text.replace(
        "import urllib.request\n",
        "import urllib.request\nimport urllib.parse\n",
        1,
    )

    print("[PASS] urllib.parse ditambahkan.")


# ================================================================
# 3. INIT MASTER ENGINE
# ================================================================

old = """        self.knowledge = (
            OfficialKnowledgeEngine()
        )

        self.intent = IntentEngine()
"""

new = """        self.knowledge = (
            OfficialKnowledgeEngine()
        )

        self.developer_core = (
            DeveloperCoreClient()
        )

        self.domain_engine = (
            MasterDomainEngine()
        )

        self.intent = IntentEngine()
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Developer Core dihubungkan ke Master Engine.")

elif "self.developer_core = (" in text:

    print("[INFO] Developer Core sudah ada di __init__.")

else:

    raise SystemExit(
        "ERROR: blok __init__ tidak ditemukan."
    )


# ================================================================
# 4. REGISTER DEVELOPER TOOLS
# ================================================================

old = """        self.tools.register(
            "knowledge_status",
            "Menampilkan status Official Production Knowledge.",
            lambda: self.knowledge.status(),
        )

        self.tools.register(
            "search_official_knowledge",
"""

new = """        self.tools.register(
            "developer_core_health",
            "Memeriksa Developer Core 8010.",
            lambda: self.developer_core.health(),
        )

        self.tools.register(
            "developer_rag_search",
            "Mencari Graph RAG dan Source RAG Developer Core.",
            lambda query, top_k=8:
                self.developer_core.search(
                    query,
                    int(top_k),
                ),
        )

        self.tools.register(
            "knowledge_status",
            "Menampilkan status Official Production Knowledge.",
            lambda: self.knowledge.status(),
        )

        self.tools.register(
            "search_official_knowledge",
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Developer Core tools ditambahkan.")

elif "developer_rag_search" in text:

    print("[INFO] Developer tools sudah ada.")

else:

    raise SystemExit(
        "ERROR: blok register tools tidak ditemukan."
    )


# ================================================================
# 5. HEALTH INTEGRATION
# ================================================================

old = """            "ollama": {
                "url": self.ollama.url,
                "model": self.ollama.model,
                "available":
                    self.ollama.health(),
            },
            "engines": {
"""

new = """            "ollama": {
                "url": self.ollama.url,
                "model": self.ollama.model,
                "available":
                    self.ollama.health(),
            },
            "developer_core": self.developer_core.health(),
            "engines": {
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Health Developer Core ditambahkan.")

elif '"developer_core": self.developer_core.health()' in text:

    print("[INFO] Health Developer Core sudah ada.")

else:

    raise SystemExit(
        "ERROR: blok health tidak ditemukan."
    )


# ================================================================
# 6. PROCESS ROUTING
# ================================================================

old = """        # --------------------------------------------------------
        # 6. OFFICIAL KNOWLEDGE
        # --------------------------------------------------------

        evidence = self.knowledge.search(
            query,
            top_k=5,
            service=intent.get(
                "service"
            ),
        )

        # --------------------------------------------------------
        # 7. POLICY
        # --------------------------------------------------------
"""

new = """        # --------------------------------------------------------
        # 6. MASTER DOMAIN ROUTING
        # --------------------------------------------------------

        master_domain = self.domain_engine.classify(
            query
        )

        developer_context = None

        # --------------------------------------------------------
        # 7. DEVELOPER CORE
        # --------------------------------------------------------

        if master_domain == "developer":

            developer_context = (
                self.developer_core.search(
                    query,
                    top_k=8,
                )
            )

            evidence = []

            developer_items = (
                developer_context.get(
                    "items",
                    []
                )
                if isinstance(
                    developer_context,
                    dict,
                )
                else []
            )

            for item in developer_items:

                evidence.append(
                    {
                        "chunk_id": None,
                        "document_id": None,
                        "chunk_index": 0,
                        "text": item.get(
                            "text",
                            "",
                        ),
                        "title": (
                            item.get("name")
                            or item.get("title")
                            or "Developer Core"
                        ),
                        "source_file": (
                            item.get("path")
                            or item.get("file")
                            or "Developer Core 8010"
                        ),
                        "service": "developer",
                        "content_type": (
                            item.get(
                                "source_type"
                            )
                            or "code"
                        ),
                        "source_status": "developer",
                        "authority": "developer",
                        "verified": 1,
                        "score": float(
                            item.get(
                                "score",
                                0.0,
                            )
                            or 0.0
                        ),
                    }
                )

        # --------------------------------------------------------
        # 8. OFFICIAL PRODUCTION KNOWLEDGE
        # --------------------------------------------------------

        else:

            evidence = self.knowledge.search(
                query,
                top_k=5,
                service=intent.get(
                    "service"
                ),
            )

        # --------------------------------------------------------
        # 9. POLICY
        # --------------------------------------------------------
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Master routing 8020 -> 8010 ditambahkan.")

elif "master_domain = self.domain_engine.classify" in text:

    print("[INFO] Master routing sudah ada.")

else:

    raise SystemExit(
        "ERROR: blok process knowledge tidak ditemukan."
    )


# ================================================================
# 7. POLICY: DEVELOPER QUERY TIDAK BOLEH TERHALANG
# ================================================================

old = """        policy = self.policy.authorize(
            query,
            intent,
            evidence,
        )
"""

new = """        if master_domain == "developer":

            policy = {
                "allowed": bool(evidence),
                "reason": (
                    "developer_core_evidence_available"
                    if evidence
                    else "developer_core_no_evidence"
                ),
                "message": (
                    None
                    if evidence
                    else
                    "Developer Core tidak menemukan "
                    "evidence yang cukup untuk pertanyaan ini."
                ),
            }

        else:

            policy = self.policy.authorize(
                query,
                intent,
                evidence,
            )
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Policy developer route ditambahkan.")

elif "developer_core_evidence_available" in text:

    print("[INFO] Policy developer route sudah ada.")

else:

    raise SystemExit(
        "ERROR: policy block tidak ditemukan."
    )


# ================================================================
# 8. REASONING DOMAIN
# ================================================================

old = """        reasoning = self.reasoning.build_plan(
            query,
            context,
            evidence,
        )
"""

new = """        context["master_domain"] = master_domain

        if developer_context is not None:
            context["developer_core"] = {
                "status":
                    developer_context.get(
                        "status"
                    ),
                "item_count":
                    len(
                        developer_context.get(
                            "items",
                            [],
                        )
                    ),
            }

        reasoning = self.reasoning.build_plan(
            query,
            context,
            evidence,
        )
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Reasoning context diperluas.")

elif 'context["master_domain"] = master_domain' in text:

    print("[INFO] Reasoning context sudah diperluas.")

else:

    raise SystemExit(
        "ERROR: reasoning block tidak ditemukan."
    )


# ================================================================
# 9. PROMPT DOMAIN
# ================================================================

old = """ATURAN MUTLAK:

1. Gunakan hanya informasi yang diberikan
   dalam SOURCE resmi.
2. Jangan membuat persyaratan,
   prosedur, biaya, waktu atau kebijakan
   yang tidak terdapat dalam SOURCE.
3. Jangan mengarang.
4. Jika informasi tidak ada dalam SOURCE,
   katakan bahwa informasi belum tersedia.
5. Jawaban harus Bahasa Indonesia.
6. Jawaban harus ringkas, jelas dan praktis.
7. Jangan mengklaim telah melakukan
   transaksi pelayanan jika tidak ada tool
   transaksi yang benar-benar dijalankan.
"""

new = """ATURAN MUTLAK:

1. Jawaban harus Bahasa Indonesia.
2. Jangan mengarang fakta.
3. Untuk SERVICE QUERY:
   gunakan hanya sumber resmi/terverifikasi.
4. Untuk DEVELOPER QUERY:
   gunakan evidence dari Developer Core 8010,
   Graph RAG, Source RAG, dan Graphify.
5. Jangan membuat persyaratan,
   prosedur, biaya, waktu atau kebijakan
   yang tidak terdapat dalam evidence.
6. Jika evidence tidak cukup,
   katakan bahwa informasi belum tersedia.
7. Jangan mengklaim melakukan transaksi
   pelayanan jika tool transaksi tidak dijalankan.
8. Untuk kode/programming, berikan solusi
   berdasarkan source/evidence yang ditemukan.
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] System prompt domain-aware diperbaiki.")

elif "Untuk DEVELOPER QUERY:" in text:

    print("[INFO] System prompt sudah domain-aware.")

else:

    raise SystemExit(
        "ERROR: system prompt tidak ditemukan."
    )


# ================================================================
# 10. EVIDENCE HEADER
# ================================================================

old = """                    f"Status: {e['source_status']}\\n"
                    f"Authority: {e['authority']}\\n"
                    f"Verified: {e['verified']}\\n"
                    f"Content:\\n{e['text']}"
"""

new = """                    f"Status: {e['source_status']}\\n"
                    f"Authority: {e['authority']}\\n"
                    f"Verified: {e['verified']}\\n"
                    f"Score: {e.get('score', 0)}\\n"
                    f"Content:\\n{e['text']}"
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Evidence score ditambahkan.")

else:

    print("[INFO] Evidence score sudah ada / block tidak perlu diubah.")


# ================================================================
# 11. RESULT DOMAIN
# ================================================================

old = """            "status": "ok",
            "answer": answer,
            "latency_seconds": elapsed,
            "intent": intent,
"""

new = """            "status": "ok",
            "answer": answer,
            "latency_seconds": elapsed,
            "master_domain": master_domain,
            "developer_core": (
                developer_context
                if master_domain == "developer"
                else None
            ),
            "intent": intent,
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Response domain metadata ditambahkan.")

elif '"master_domain": master_domain' in text:

    print("[INFO] Response domain metadata sudah ada.")

else:

    raise SystemExit(
        "ERROR: result block tidak ditemukan."
    )


# ================================================================
# 12. BLOCKED RESULT DOMAIN
# ================================================================

old = """            result = {
                "status": "blocked",
                "answer": answer,
                "intent": intent,
"""

new = """            result = {
                "status": "blocked",
                "answer": answer,
                "master_domain": master_domain,
                "developer_core": (
                    developer_context
                    if master_domain == "developer"
                    else None
                ),
                "intent": intent,
"""

if old in text:

    text = text.replace(
        old,
        new,
        1,
    )

    print("[PASS] Blocked response domain metadata ditambahkan.")

elif '"master_domain": master_domain' in text:

    print("[INFO] Blocked response metadata sudah ada.")

else:

    print("[WARN] Blocked response metadata tidak ditemukan.")


# ================================================================
# 13. SAVE
# ================================================================

src.write_text(
    text,
    encoding="utf-8",
)

print()
print("=" * 72)
print(" PATCH SELESAI")
print("=" * 72)
print()
print(f"Backup dibuat : {backup.name}")
print(f"Source        : {src.name}")
print()
