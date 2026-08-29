@echo off
echo ============================================================
echo   Starting SIH26028 Dynamic Train ETA Forecast System
echo ============================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start cmd /k "cd /d %~dp0\backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload"

timeout /t 3 /nobreak > NUL

echo [2/2] Starting React Vite Operations Dashboard on http://localhost:3000...
start cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo System initialized successfully!
echo Backend Docs: http://127.0.0.1:8000/docs
echo Operations Dashboard: http://localhost:3000
