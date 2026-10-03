@echo off
cd /d C:\Users\dmaza\mcp-starter
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\service\nusantara-service.ps1" stop
pause
