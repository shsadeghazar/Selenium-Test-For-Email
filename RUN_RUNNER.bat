@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found.
    echo First run install_all_in_venv.bat
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "ui_runner.py"
if errorlevel 1 pause

