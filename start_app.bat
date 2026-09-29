@echo off
set "PATH=C:\Program Files\nodejs;%PATH%"
echo ============================================================
echo   Starting SIH26028 Dynamic Train ETA Forecast System
echo ============================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "FastAPI Backend" /D "%~dp0backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload"

ping -n 4 127.0.0.1 >nul

echo [2/2] Starting React Vite Operations Dashboard on http://localhost:3000...
start "React Vite Frontend" /D "%~dp0frontend" cmd /k "npm.cmd run dev"

echo.
echo System initialized successfully!
echo Backend Docs: http://127.0.0.1:8000/docs
echo Operations Dashboard: http://localhost:3000
