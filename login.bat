@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   Launching LinkedIn Login Assistant
echo ========================================================

if exist "%~dp0linkedin_outreach\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0linkedin_outreach\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -m linkedin_outreach.cli login
pause
