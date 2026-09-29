# SIH26028 One-Command Local Startup Script (Windows PowerShell)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting SIH26028 Dynamic Train ETA Forecast System " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Start Backend in new process or window
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "Set-Location backend; .\venv\Scripts\python.exe run.py"

# Wait 3 seconds for backend server startup
Start-Sleep -Seconds 3

# 2. Start Frontend in new process or window
Write-Host "[2/2] Starting React Vite Operations Dashboard on http://localhost:3000..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "`$env:PATH = 'C:\Program Files\nodejs;' + `$env:PATH; Set-Location frontend; & 'C:\Program Files\nodejs\npm.cmd' run dev"

Write-Host ""
Write-Host "System initialized successfully!" -ForegroundColor Green
Write-Host "Backend Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "Operations Dashboard: http://localhost:3000" -ForegroundColor Cyan
