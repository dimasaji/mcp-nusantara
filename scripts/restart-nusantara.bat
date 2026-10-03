@echo off

call "%~dp0stop-nusantara.bat"

timeout /t 2 /nobreak >nul

call "%~dp0start-nusantara.bat"