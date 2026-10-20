@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0nusantara-service.ps1" stop %*
