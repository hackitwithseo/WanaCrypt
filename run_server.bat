@echo off
cd /d "%~dp0"
python server.py
echo.
echo ---- exit code %errorlevel% ----
pause