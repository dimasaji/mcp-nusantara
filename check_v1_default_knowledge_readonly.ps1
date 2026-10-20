# Nusantara V1 - Read-only default knowledge database inspection
# Run from the repository root: powershell -ExecutionPolicy Bypass -File .\check_v1_default_knowledge_readonly.ps1
# This script does not write to the database or modify project files.

$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' NUSANTARA V1 - DEFAULT KNOWLEDGE DATABASE CHECK (READ ONLY)' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

$projectRoot = (Get-Location).Path
$dbPath = Join-Path $projectRoot 'data\knowledge\nusantara_knowledge.db'

Write-Host "Project root : $projectRoot"
Write-Host "Database     : $dbPath"

if (-not (Test-Path -LiteralPath $dbPath -PathType Leaf)) {
    Write-Host 'RESULT: DATABASE_NOT_FOUND' -ForegroundColor Red
    Write-Host 'Jalankan skrip dari root repository Nusantara.'
    exit 2
}

$dbInfo = Get-Item -LiteralPath $dbPath
Write-Host "File size    : $($dbInfo.Length) bytes"
Write-Host "Last modified: $($dbInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"

# Pass the absolute path through the environment; Python opens SQLite in read-only mode.
$env:NUSANTARA_V1_KB_DB = $dbPath

$pythonCode = @'
import os
import sqlite3
import sys
from pathlib import Path

raw_path = os.environ.get("NUSANTARA_V1_KB_DB")
if not raw_path:
    print("RESULT: DATABASE_PATH_NOT_PROVIDED")
    sys.exit(2)

path = Path(raw_path).resolve()
# pathlib.as_uri() correctly escapes the absolute path, including Windows drive letters.
uri = path.as_uri() + "?mode=ro"

try:
    con = sqlite3.connect(uri, uri=True, timeout=5)
    con.execute("PRAGMA query_only = ON")
    try:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        print("\n--- DATABASE STRUCTURE ---")
        print("Database exists : YES")
        print("Read-only mode  : YES")
        print("documents table :", "YES" if "documents" in tables else "NO")

        if "documents" not in tables:
            print("RESULT: REQUIRED_TABLE_MISSING")
            sys.exit(3)

        columns = {
            row[1]
            for row in con.execute("PRAGMA table_info(documents)").fetchall()
        }
        print("Available columns:", ", ".join(sorted(columns)))
        required = {"document_id", "title"}
        missing = required - columns
        if missing:
            print("RESULT: REQUIRED_COLUMNS_MISSING:", ", ".join(sorted(missing)))
            sys.exit(3)

        selected = ["document_id", "title"]
        has_source = "source" in columns
        if has_source:
            selected.append("source")

        sql = (
            "SELECT " + ", ".join(selected) + " FROM documents "
            "WHERE document_id LIKE ? OR title LIKE ?"
        )
        params = ("%TNG-KTPEL-001%", "%KTP%pemula%")
        rows = con.execute(sql, params).fetchall()

        print("\n--- SEARCH: DOCUMENT ID / TITLE ---")
        if not rows:
            print("No document matched ID TNG-KTPEL-001 or title pattern KTP/pemula.")
        else:
            for index, row in enumerate(rows, start=1):
                print(f"\nRecord {index}")
                print("document_id:", row[0])
                print("title      :", row[1])
                if has_source:
                    preview = (row[2] or "").replace("\r", " ").replace("\n", " ")
                    print("source preview:", preview[:300] or "[EMPTY]")

        # Also search for the exact requirements phrase as a separate diagnostic.
        if has_source:
            evidence_sql = (
                "SELECT document_id, title FROM documents "
                "WHERE source LIKE ?"
            )
            evidence_rows = con.execute(
                evidence_sql, ("%Fotocopy kartu keluarga%",)
            ).fetchall()
            print("\n--- SEARCH: REQUIREMENTS PHRASE ---")
            if evidence_rows:
                for doc_id, title in evidence_rows:
                    print(f"MATCH: {doc_id} | {title}")
            else:
                print("No source text matched 'Fotocopy kartu keluarga'.")

        print("\nRESULT:", "MATCH_FOUND" if rows else "NO_MATCH_FOUND")
    finally:
        con.close()
except sqlite3.Error as exc:
    print("RESULT: SQLITE_READ_ERROR")
    print(f"Details: {exc}")
    sys.exit(4)
'@

$tempPython = Join-Path ([System.IO.Path]::GetTempPath()) ("nusantara_v1_kb_check_" + [guid]::NewGuid().ToString('N') + '.py')
try {
    # A temporary UTF-8 script avoids PowerShell-to-native stdin encoding and indentation issues.
    Set-Content -LiteralPath $tempPython -Value $pythonCode -Encoding UTF8
    python $tempPython
    $pythonExitCode = $LASTEXITCODE
} finally {
    Remove-Item Env:\NUSANTARA_V1_KB_DB -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempPython -Force -ErrorAction SilentlyContinue
}

if ($pythonExitCode -ne 0) {
    Write-Host "Python inspection exited with code $pythonExitCode" -ForegroundColor Yellow
    exit $pythonExitCode
}

Write-Host ''
Write-Host 'Selesai. Database dibuka dalam mode baca-saja; tidak ada perubahan yang diminta.' -ForegroundColor Green
