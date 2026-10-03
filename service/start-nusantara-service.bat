@echo off
title Nusantara AI Service - START

cd /d C:\Users\dmaza\mcp-starter

echo ==========================================
echo       NUSANTARA AI SERVICE
echo              STARTING
echo ==========================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass ^
  -WindowStyle Hidden ^
  -File "C:\Users\dmaza\mcp-starter\service\nusantara-supervisor.ps1"

echo.
echo Nusantara AI Supervisor stopped.
pause