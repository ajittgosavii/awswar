# Create backend starter
@"
@echo off
cd /d C:\Apps\waf-scanner-complete\backend
call venv\Scripts\activate.bat
echo Starting FastAPI backend on port 8000...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"@ | Out-File -FilePath "C:\Apps\waf-scanner-complete\start_backend.bat" -Encoding ASCII

# Create frontend starter
@"
@echo off
cd /d C:\Apps\waf-scanner-complete\frontend
echo Starting React frontend on port 3000...
npm run dev
"@ | Out-File -FilePath "C:\Apps\waf-scanner-complete\start_frontend.bat" -Encoding ASCII

# Create combined starter
@"
@echo off
echo Starting AWS WAF Scanner...
start "Backend" cmd /k "C:\Apps\waf-scanner-complete\start_backend.bat"
timeout /t 5 /nobreak > nul
start "Frontend" cmd /k "C:\Apps\waf-scanner-complete\start_frontend.bat"
timeout /t 3 /nobreak > nul
start http://localhost:3000
"@ | Out-File -FilePath "C:\Apps\waf-scanner-complete\start_waf_scanner.bat" -Encoding ASCII

Write-Host "Startup scripts created!" -ForegroundColor Green