@echo off
title Nusantara AI - STATUS

echo ==========================================
echo       NUSANTARA AI STATUS
echo ==========================================
echo.

echo [OLLAMA]
tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe"

if errorlevel 1 (
    echo Ollama: STOPPED
) else (
    echo Ollama: RUNNING
)

echo.
echo [NUSANTARA CORE]

netstat -ano | findstr ":8000" | findstr "LISTENING"

if errorlevel 1 (
    echo Nusantara Core: STOPPED
) else (
    echo Nusantara Core: RUNNING
)

echo.
echo [API]
curl -s http://127.0.0.1:8000/v1/health

echo.
echo.
echo ==========================================

pause