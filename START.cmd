@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto python_error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error
:run
".venv\Scripts\python.exe" -c "import PIL, imageio_ffmpeg" >nul 2>&1
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto install_error
)
".venv\Scripts\python.exe" app.py
pause
exit /b
:python_error
echo Install Python 3.11 or newer from https://www.python.org/downloads/windows/
echo Enable "Add python.exe to PATH", then run START.cmd again.
pause
exit /b 1
:install_error
echo Dependencies could not be installed. Check your internet connection.
echo Run START.cmd again to retry.
pause
exit /b 1
