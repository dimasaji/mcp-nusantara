@echo off
:: ==============================================================================
:: Nusantara V1 — Startup Script (Windows / PC Nusantara)
:: Menjalankan backend Lean Intelligence Engine + frontend dev server di localhost.
:: Tidak menggunakan Tailscale / Cloudflare. Tidak dibuka ke publik.
:: ==============================================================================
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

:: --- Environment ---
if not exist .env (
  copy .env.example .env >nul
  echo [INFO] .env dibuat dari .env.example
)
for /f "usebackq delims=" %%a in (.env) do (
  set "%%a"
)

if not defined NUSANTARA_HOST set NUSANTARA_HOST=127.0.0.1
if not defined NUSANTARA_PORT set NUSANTARA_PORT=8021
if not defined OLLAMA_URL set OLLAMA_URL=http://127.0.0.1:11434
if not defined OLLAMA_MODEL set OLLAMA_MODEL=llama3.2:1b

echo ============================================================
echo Nusantara V1 — Lean Intelligence Engine (Windows)
echo ============================================================
echo Backend  : http://%NUSANTARA_HOST%:%NUSANTARA_PORT%
echo Ollama   : %OLLAMA_URL% / %OLLAMA_MODEL%
echo ============================================================

:: --- Ollama ---
where ollama >nul 2>&1
if %errorlevel% neq 0 (
  echo [WARN] Ollama tidak ditemukan. LLM lokal tidak tersedia; backend tetap jalan.
) else (
  tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find "ollama.exe" >nul
  if %errorlevel% neq 0 (
    echo [INFO] Menyalakan Ollama...
    start /b ollama serve
    timeout /t 3 >nul
  )
  echo [OK] Ollama di %OLLAMA_URL%
)

:: --- Backend (Python venv) ---
if exist ".venv-nusantara\Scripts\activate.bat" (
  call ".venv-nusantara\Scripts\activate.bat"
) else (
  echo [WARN] Virtual environment tidak ditemukan. Jalankan install.sh terlebih dahulu.
)
echo [INFO] Menyalakan backend di port %NUSANTARA_PORT%...
start /b python lia_engine.py >nul 2>&1
timeout /t 3 >nul

:: --- Frontend ---
if exist "frontend\node_modules" (
  echo [INFO] Menyalakan frontend dev server (port 5173)...
  start /b "" cmd /c "cd frontend && npm run dev >nul 2>&1"
  echo [OK] Frontend: http://localhost:5173
) else (
  echo [WARN] Frontend node_modules tidak ditemukan. Jalankan install.sh, lalu:
  echo         cd frontend && npm run dev
  echo         atau build: cd frontend && npm run build
)

echo.
echo Semua layanan berjalan di localhost (tidak dibuka ke publik).
echo Log: /tmp-style; lihat console atau gunakan file log secara manual.
pause
