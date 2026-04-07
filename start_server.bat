@echo off
setlocal

echo ==========================================
echo  Starting AI Newsletter Local API Server
echo ==========================================

:: Check if venv exists
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

:: Check if Flask is installed
%PYTHON% -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo Flask not found. Installing dependencies...
    %PYTHON% -m pip install Flask Flask-Cors
)

:: Run the server
%PYTHON% api.py

pause
