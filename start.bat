@echo off
echo ====================================
echo   MEM Study System - Starting...
echo ====================================
echo.

:: Start Backend API
echo [1/2] Starting Backend API (port 8000)...
start "MEM Backend" cmd /k "cd /d %~dp0 && python scripts/api.py"

:: Wait for backend to start
timeout /t 2 /nobreak > nul

:: Start Frontend
echo [2/2] Starting Frontend (port 5173)...
cd /d %~dp0web
call npm run dev

pause
