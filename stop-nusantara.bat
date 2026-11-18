@echo off
echo Nusantara V1 - Stop
taskkill /FI "WINDOWTITLE eq Nusantara Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Nusantara Frontend*" /F >nul 2>&1
echo Stopped Nusantara services
