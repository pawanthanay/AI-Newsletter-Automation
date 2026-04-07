@echo off
setlocal

echo ==========================================
echo  AI Newsletter Bot - Windows Setup
echo ==========================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8+.
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

:: Upgrade pip and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Some dependencies failed to install. Please check the logs.
)

:: Create directories
if not exist "history" mkdir history
if not exist "logs" mkdir logs

echo.
echo ==========================================
echo  Setup complete!
echo ==========================================
echo Next steps:
echo   1. Configure config.yaml
echo   2. Run demo: python main.py --demo
echo   3. Start server: start_server.bat
echo ==========================================
pause
