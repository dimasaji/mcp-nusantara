@echo off
echo Nusantara V1 - Doctor
echo.
python --version 2>&1
curl -s http://127.0.0.1:8000/v1/health 2>nul && echo Backend: OK || echo Backend: FAIL
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1 && echo Ollama: OK || echo Ollama: FAIL
if exist ".venv\Scripts\python.exe" (echo Python venv: OK) else (echo Python venv: FAIL)
echo Doctor check complete
