@echo off
setlocal
cd /d "%~dp0"

echo ======================================================
echo  VentureLens - Startup Idea Validation Assistant
echo ======================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found.
  echo Install Python 3.11 or newer from https://www.python.org/downloads/
  echo During installation, enable the option to add Python to PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Could not create the virtual environment.
    pause
    exit /b 1
  )
) else (
  echo [1/3] Virtual environment already exists.
)

echo [2/3] Installing / checking dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo WARNING: pip upgrade failed; attempting to install project dependencies anyway.
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Dependency installation failed.
  echo Check your internet connection and try again.
  pause
  exit /b 1
)

echo [3/3] Starting the application...
echo.
echo Open http://127.0.0.1:5000 in your browser.
echo Keep this window open while using the app. Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" app.py
if errorlevel 1 (
  echo.
  echo The application stopped with an error. Review the message above.
  pause
  exit /b 1
)
endlocal
