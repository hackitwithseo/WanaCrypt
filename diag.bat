@echo off
echo === output folder ===
dir /b output 2>nul
echo.
echo === appdata dirs ===
dir /b "%APPDATA%\w*" 2>nul
echo.
echo === logs ===
for /d %%d in ("%APPDATA%\w*") do (
  echo --- %%d ---
  type "%%d\run.log" 2>nul
  type "%%d\net.log" 2>nul
  type "%%d\main.log" 2>nul
)
echo.
echo === stub logs ===
type "%TEMP%\wnk_err.log" 2>nul
type "%TEMP%\wnk_main.log" 2>nul
echo.
echo === defender detections ===
powershell -NoProfile -Command "Get-MpThreatDetection | Select-Object -Last 5 | Format-List InitialDetectionTime,ThreatName,Resources"
pause