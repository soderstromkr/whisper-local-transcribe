@echo off
REM Activate conda base environment and run the app from the current folder

REM Try to find conda and activate base
call conda activate base 2>nul
if errorlevel 1 (
    echo ERROR: Could not activate conda base environment.
    echo Make sure Anaconda or Miniconda is installed and "conda" is on your PATH.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import faster_whisper" 2>nul
if errorlevel 1 (
    echo First run detected - running installer...
    python install.py
    echo.
)

echo Starting Local Transcribe...
python app.py
