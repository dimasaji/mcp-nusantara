@echo off
setlocal
cd /d "%~dp0"
echo Nusantara V1 - Startup
if not exist "%~dp0.venv\Scripts\python.exe" (echo [ERROR] Local Python environment not found & exit /b 1)
if not exist "%~dp0frontend\package.json" (echo [ERROR] Frontend package not found & exit /b 1)
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (start "" ollama serve & timeout /t 5 /nobreak >nul)
echo [1/3] Starting Backend (port 8000)...
start "Nusantara Backend" /D "%~dp0" cmd /c .venv\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000 --log-level warning
timeout /t 8 /nobreak >nul
curl -fsS http://127.0.0.1:8000/v1/health >nul 2>&1
if errorlevel 1 (echo [ERROR] Backend failed & exit /b 1)
echo [OK] Backend running
echo [2/3] Starting Frontend (port 5180)...
start "Nusantara Frontend" /D "%~dp0frontend" cmd /c npm run dev -- --port 5180
timeout /t 5 /nobreak >nul
echo [OK] Frontend starting
echo [3/3] Health Check complete
echo Backend: http://127.0.0.1:8000/v1/health
echo Frontend: http://127.0.0.1:5180
echo Ollama: http://127.0.0.1:11434
echo Nusantara V1 Started Successfully
