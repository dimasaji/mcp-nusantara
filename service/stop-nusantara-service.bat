@echo off
title Nusantara AI Service - STOP

echo ==========================================
echo       STOP NUSANTARA AI
echo ==========================================
echo.

taskkill /FI "WINDOWTITLE eq Nusantara AI Supervisor*" /F >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Stopping Nusantara Core PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

taskkill /IM ollama.exe /F >nul 2>&1

echo.
echo Nusantara AI telah dihentikan.
echo.
pause