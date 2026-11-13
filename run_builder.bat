@echo off
cd /d "%~dp0"
python builder.py
echo.
echo ---- exit code %errorlevel% ----
pause