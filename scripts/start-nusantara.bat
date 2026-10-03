@echo off
setlocal

title Nusantara AI - START

set "ROOT=C:\Users\dmaza\mcp-starter"
set "VENV=%ROOT%\.venv"
set "LOG=%ROOT%\data\logs"

if not exist "%LOG%" mkdir "%LOG%"

echo ==========================================
echo       NUSANTARA AI STARTING
echo ==========================================
echo.

cd /d "%ROOT%"

echo [1/4] Checking Ollama...

where ollama >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama tidak ditemukan.
    pause
    exit /b 1
)

echo Ollama ditemukan.

echo.
echo [2/4] Starting Ollama...

tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe" >nul

if errorlevel 1 (
    start "" /MIN ollama serve
    timeout /t 3 /nobreak >nul
    echo Ollama started.
) else (
    echo Ollama sudah berjalan.
)

echo.
echo [3/4] Checking Python environment...

if not exist "%VENV%\Scripts\python.exe" (
    echo ERROR: Virtual environment tidak ditemukan:
    echo %VENV%
    pause
    exit /b 1
)

echo Python environment OK.

echo.
echo [4/4] Starting Nusantara Core...

tasklist /FI "WINDOWTITLE eq Nusantara Core*" | find /I "python.exe" >nul

if not errorlevel 1 (
    echo Nusantara Core kemungkinan sudah berjalan.
    echo.
    echo API:
    echo http://127.0.0.1:8000
    echo Swagger:
    echo http://127.0.0.1:8000/docs
    pause
    exit /b 0
)

start "Nusantara Core" cmd /k ^
"cd /d %ROOT% && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo       NUSANTARA AI RUNNING
echo ==========================================
echo.
echo API     : http://127.0.0.1:8000
echo Swagger : http://127.0.0.1:8000/docs
echo.
echo Ollama  : http://127.0.0.1:11434
echo.

pause