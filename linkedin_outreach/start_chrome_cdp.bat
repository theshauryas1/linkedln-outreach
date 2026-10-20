@echo off
setlocal
echo ========================================================
echo   Launching Chrome with CDP on Port 18800
echo ========================================================
set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
set "PROFILE_DIR=%~dp0chrome_profile"

start "" "%CHROME_PATH%" --remote-debugging-port=18800 --user-data-dir="%PROFILE_DIR%" --disable-blink-features=AutomationControlled https://www.linkedin.com/feed/

echo [SUCCESS] Chrome launched on port 18800!
echo Our automation agent can now connect directly to this session.
