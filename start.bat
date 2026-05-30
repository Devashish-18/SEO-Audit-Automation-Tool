@echo off
echo ========================================
echo  SEO Audit Automation Tool - Startup
echo ========================================
echo.
echo Starting backend API on port 5000...
echo Starting web server on port 8000...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Start API in background
start "SEO Audit API" cmd /k python api.py

REM Wait a moment for API to start
timeout /t 2 /nobreak

REM Start HTTP server in background
start "SEO Audit Web Server" cmd /k python -m http.server 8000

echo.
echo ========================================
echo  ✅ Services Started!
echo ========================================
echo.
echo 🌐 Open in browser: http://localhost:8000
echo.
echo API Backend: http://localhost:5000
echo Web Server:  http://localhost:8000
echo.
echo Close the popup windows to stop the services.
echo ========================================
echo.
pause
