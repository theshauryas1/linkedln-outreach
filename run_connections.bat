@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0linkedin_outreach\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0linkedin_outreach\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

if "%1"=="login" (
    "%PYTHON_EXE%" -m linkedin_outreach.cli login
) else if "%1"=="status" (
    "%PYTHON_EXE%" -m linkedin_outreach.cli status
) else if "%1"=="scrape" (
    "%PYTHON_EXE%" -m linkedin_outreach.cli connections %*
) else if "%1"=="run" (
    "%PYTHON_EXE%" -m linkedin_outreach.cli connections %*
) else if "%1"=="serve" (
    "%PYTHON_EXE%" -m linkedin_outreach.cli serve %2 %3
) else (
    "%PYTHON_EXE%" -m linkedin_outreach.cli connections run %*
)
