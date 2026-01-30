@echo off
echo Starting Face Auth System...

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not recognized. 
    echo Please make sure Python is installed and added to your SYSTEM PATH.
    echo.
    pause
    exit /b
)

echo Python found. Starting application...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
