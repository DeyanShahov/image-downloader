@echo off
echo ========================================
echo   Image Downloader - Setup ^& Start
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed!
        echo Please install Python 3.8+ from python.org
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo [OK] Python found: %PYTHON_CMD%

REM Create virtual environment if it doesn't exist
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [*] Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo.
echo [*] Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [*] Installing dependencies ^(this may take a minute^)...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)

REM Kill old processes on port 5000
echo.
echo [*] Stopping old processes on port 5000...
netstat -ano | findstr ":5000" | for /f "tokens=5" %%a in ('more') do (
    echo Killing process %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Start the application
echo.
echo [*] Starting Image Downloader...
start http://127.0.0.1:5000
python app.py

pause
