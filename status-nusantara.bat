@echo off
echo Nusantara V1 - Status
echo.
curl -s http://127.0.0.1:8000/v1/health 2>nul
echo.
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1 && echo Ollama: RUNNING || echo Ollama: NOT RUNNING
