@echo off
setlocal
cd /d "%~dp0\.."

if exist "%~dp0runtime\python.exe" (
    set "PYTHON_EXE=%~dp0runtime\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else if exist "C:\Users\thesh\AppData\Local\Microsoft\WindowsApps\python.exe" (
        set "PYTHON_EXE=C:\Users\thesh\AppData\Local\Microsoft\WindowsApps\python.exe"
    )
)

echo ========================================================
echo   Starting LinkedIn Outreach Daily Pipeline (9:00 AM)
echo ========================================================
"%PYTHON_EXE%" -m linkedin_outreach.cli run --invites 20 --messages 20
echo ========================================================
echo   Run complete.
echo ========================================================
