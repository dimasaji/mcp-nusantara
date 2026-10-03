@echo off
title Nusantara AI - STOP

echo ==========================================
echo       STOP NUSANTARA AI
echo ==========================================
echo.

echo [1/2] Stopping Nusantara Core...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Killing PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo [2/2] Stopping Ollama...

taskkill /IM ollama.exe /F >nul 2>&1

echo.
echo ==========================================
echo       NUSANTARA AI STOPPED
echo ==========================================
echo.

pause