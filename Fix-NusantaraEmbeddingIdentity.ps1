$ErrorActionPreference = 'Stop'
$Root = 'C:\Users\dmaza\mcp-starter'
Set-Location $Root
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $Root ".backup-embedding-identity-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null
Copy-Item .\app\knowledge\store.py (Join-Path $backup 'store.py')
Copy-Item .\app\knowledge\rag.py (Join-Path $backup 'rag.py')

$patcher = @'
from pathlib import Path
import re
root = Path.cwd()
sp = root / 'app/knowledge/store.py'
rp = root / 'app/knowledge/rag.py'
s = sp.read_text(encoding='utf-8')
r = rp.read_text(encoding='utf-8')

# Patch only SQLiteVectorStore.search_similarity, not similarly named methods in other classes.
class_match = re.search(r'(?m)^class SQLiteVectorStore\b', s)
if not class_match:
    raise SystemExit('ABORT: class SQLiteVectorStore tidak ditemukan; file tidak diubah.')
next_class = re.search(r'(?m)^class \w+', s[class_match.end():])
class_end = class_match.end() + next_class.start() if next_class else len(s)
prefix, block, suffix = s[:class_match.end()], s[class_match.end():class_end], s[class_end:]
store_pattern = r'(?ms)^    def search_similarity\(.*?^    def search_lexical\('
store_replacement = '''    def search_similarity(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        embedding_model: Optional[str] = None,
    ) -> List[tuple]:
        """Search only vectors matching the verified model and query dimension."""
        if not query_embedding or not embedding_model or not str(embedding_model).strip():
            return []
        results = []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM chunks
                WHERE embedding_dimension = ? AND embedding_model = ?
                """,
                (len(query_embedding), str(embedding_model).strip()),
            ).fetchall()
        for row in rows:
            vector = self._deserialize_embedding(row["embedding"], row["embedding_dimension"])
            if len(vector) != len(query_embedding):
                continue
            score = self._similarity(query_embedding, vector)
            results.append((self._row_to_chunk(row), score))
        results.sort(key=lambda item: item[1], reverse=True)
        return results[:max(1, int(top_k))]

    def search_lexical('''
block2, ns = re.subn(store_pattern, store_replacement, block, count=1)
if ns != 1:
    raise SystemExit('ABORT: fungsi SQLiteVectorStore.search_similarity tidak cocok; file tidak diubah.')
s2 = prefix + block2 + suffix

# Find the ingest embedding_data dict regardless of its nesting indentation.
ingest_pattern = r'(?m)^(?P<i>[ \t]*)embedding_data = \{\n(?:(?!^[ \t]*\}).*\n)*?^[ \t]*\}'
ingest_match = re.search(ingest_pattern, r)
if not ingest_match:
    raise SystemExit('ABORT: blok embedding_data tidak ditemukan; file tidak diubah.')
i = ingest_match.group('i')
ingest_replacement = (
    f'{i}embedding_verified = (\n'
    f'{i}    self._embedding_adapter is not None\n'
    f'{i}    and self._embedding is self._embedding_adapter\n'
    f'{i}    and self._config.embedding_model == "indobenchmark/indobert-base-p1"\n'
    f'{i}    and self._config.embedding_dimension == 768\n'
    f'{i})\n'
    f'{i}embedding_data = {{\n'
    f'{i}    "vector": embedding_vector,\n'
    f'{i}    "dimension": len(embedding_vector),\n'
    f'{i}    "model": self._config.embedding_model if embedding_verified else "unknown",\n'
    f'{i}}}'
)
r2 = r[:ingest_match.start()] + ingest_replacement + r[ingest_match.end():]

# Match the known semantic retrieval block while tolerating indentation changes.
query_pattern = r"(?ms)^(?P<i>[ \t]*)query_embedding = self\._embedding\(query_text\)\n(?P=i)trace\['stage'\] = 'semantic_search'\n(?P=i)semantic_candidates = self\._store\.search_similarity\(\n(?P=i)    query_embedding,\n(?P=i)    candidate_k,\n(?P=i)\)"
query_match = re.search(query_pattern, r2)
if not query_match:
    raise SystemExit('ABORT: blok semantic_search tidak ditemukan; file tidak diubah.')
i = query_match.group('i')
query_replacement = (
    f'{i}query_embedding = self._embedding(query_text)\n'
    f'{i}trace[\'stage\'] = \'semantic_search\'\n'
    f'{i}embedding_verified = (\n'
    f'{i}    self._embedding_adapter is not None\n'
    f'{i}    and self._embedding is self._embedding_adapter\n'
    f'{i}    and self._config.embedding_model == "indobenchmark/indobert-base-p1"\n'
    f'{i}    and self._config.embedding_dimension == 768\n'
    f'{i})\n'
    f'{i}if not embedding_verified:\n'
    f'{i}    semantic_candidates = []\n'
    f'{i}elif isinstance(self._store, SQLiteVectorStore):\n'
    f'{i}    semantic_candidates = self._store.search_similarity(\n'
    f'{i}        query_embedding, candidate_k,\n'
    f'{i}        embedding_model=self._config.embedding_model,\n'
    f'{i}    )\n'
    f'{i}else:\n'
    f'{i}    semantic_candidates = self._store.search_similarity(query_embedding, candidate_k)'
)
r3 = r2[:query_match.start()] + query_replacement + r2[query_match.end():]

# Verify both edits are present before writing either source file.
if 'embedding_dimension = ? AND embedding_model = ?' not in s2:
    raise SystemExit('ABORT: verifikasi filter store gagal; file tidak diubah.')
if 'self._config.embedding_model if embedding_verified else "unknown"' not in r3:
    raise SystemExit('ABORT: verifikasi label embedding gagal; file tidak diubah.')
if 'embedding_model=self._config.embedding_model' not in r3:
    raise SystemExit('ABORT: verifikasi filter query gagal; file tidak diubah.')
sp.write_text(s2, encoding='utf-8')
rp.write_text(r3, encoding='utf-8')
print('PATCH_APPLIED')
'@

try {
    $patcher | python -
    if ($LASTEXITCODE -ne 0) { throw 'Patch gagal; kedua file sumber tidak ditulis.' }

    Write-Host "`n=== Sampel 1/3: profil + integrasi konfigurasi ===" -ForegroundColor Cyan
    python -m pytest .\tests\test_effective_rag_profile.py .\tests\test_configuration_integration.py -q
    if ($LASTEXITCODE -ne 0) { throw 'Sampel 1 gagal.' }

    Write-Host "`n=== Sampel 2/3: adapter RAG + evidence pipeline ===" -ForegroundColor Cyan
    $tests = @('.\tests\test_weip_rag_adapter.py', '.\tests\test_web_evidence_pipeline.py') | Where-Object { Test-Path $_ }
    if ($tests.Count -gt 0) {
        python -m pytest @tests -q
        if ($LASTEXITCODE -ne 0) { throw 'Sampel 2 gagal.' }
    } else { throw 'File tes untuk Sampel 2 tidak ditemukan.' }

    Write-Host "`n=== Sampel 3/3: validasi sintaks Python ===" -ForegroundColor Cyan
    python -c "import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['app/knowledge/store.py','app/knowledge/rag.py']]; print('PASS: kedua file lolos parsing Python')"
    if ($LASTEXITCODE -ne 0) { throw 'Sampel 3 gagal.' }

    Write-Host "`nSELESAI: ketiga sampel lulus. Cadangan: $backup" -ForegroundColor Green
}
catch {
    Write-Host "`nBERHENTI: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Cadangan: $backup" -ForegroundColor Yellow
    Write-Host 'Jika patch diterapkan tetapi tes gagal, pulihkan kedua file sumber dari folder cadangan.' -ForegroundColor Yellow
    exit 1
}
