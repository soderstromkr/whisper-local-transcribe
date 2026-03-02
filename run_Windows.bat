@echo off
REM Create .venv on first run if it doesn't exist
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Is Python installed and on PATH?
        pause
        exit /b 1
    )
)

set PYTHON=.venv\Scripts\python.exe

REM Check if dependencies are installed
%PYTHON% -c "import faster_whisper" 2>nul
if errorlevel 1 (
    echo First run detected - running installer...
    %PYTHON% install.py
    echo.
)
echo Starting Local Transcribe...
%PYTHON% app.py