@echo off
REM Activate conda base environment and run the app from the current folder
REM Works even when conda is NOT on PATH (no admin rights / user install)

set CONDA_ACTIVATE=

REM Search common Anaconda / Miniconda install locations
for %%P in (
    "%USERPROFILE%\Anaconda3\Scripts\activate.bat"
    "%USERPROFILE%\anaconda3\Scripts\activate.bat"
    "%USERPROFILE%\Miniconda3\Scripts\activate.bat"
    "%USERPROFILE%\miniconda3\Scripts\activate.bat"
    "%LOCALAPPDATA%\Continuum\anaconda3\Scripts\activate.bat"
    "%PROGRAMDATA%\Anaconda3\Scripts\activate.bat"
    "%PROGRAMFILES%\Anaconda3\Scripts\activate.bat"
) do (
    if exist %%P (
        set CONDA_ACTIVATE=%%P
        goto :found
    )
)

echo ERROR: Could not find a conda installation.
echo Please open Anaconda Prompt manually and run:  python app.py
pause
exit /b 1

:found
echo Found conda: %CONDA_ACTIVATE%
call "%CONDA_ACTIVATE%" base
if errorlevel 1 (
    echo ERROR: Failed to activate conda base environment.
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
