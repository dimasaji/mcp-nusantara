$ErrorActionPreference = "Stop"
Write-Host "Starting Nusantara Core + Hermes..."
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) { Copy-Item ".env.example" ".env" }
if (-not (Test-Path ".venv")) { py -3.12 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe run_tests.py
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
