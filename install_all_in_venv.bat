@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Mail Runner - Install Dependencies

set "VENV_DIR=%CD%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

echo ============================================================
echo   Mail Runner - Install everything inside .venv
echo ============================================================
echo.

if exist "%VENV_PYTHON%" goto :venv_ready

echo [1/5] Creating .venv...
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv "%VENV_DIR%"
    goto :venv_created
)

where python >nul 2>&1
if errorlevel 1 goto :python_missing
python -m venv "%VENV_DIR%"

:venv_created
if not exist "%VENV_PYTHON%" goto :venv_failed

:venv_ready
echo [1/5] Using: "%VENV_PYTHON%"

echo.
echo [2/5] Upgrading pip tools...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :install_failed

echo.
echo [3/5] Installing runtime and build dependencies...
"%VENV_PYTHON%" -m pip install --upgrade "selenium>=4.27,<5" "jdatetime>=5,<6" "pyinstaller>=6,<7"
if errorlevel 1 goto :install_failed

echo.
echo [4/5] Checking installed packages...
"%VENV_PYTHON%" -m pip check
if errorlevel 1 goto :verify_failed

echo.
echo [5/5] Verifying Runner imports...
"%VENV_PYTHON%" -c "import tkinter, jdatetime, selenium, PyInstaller; from selenium import webdriver; from selenium.webdriver.chrome.webdriver import WebDriver; from selenium.webdriver.chrome.options import Options; from selenium.webdriver.chrome.service import Service; print('All required imports are OK')"
if errorlevel 1 goto :verify_failed

echo.
echo ============================================================
echo   SUCCESS: Everything is installed inside .venv
echo ============================================================
echo.
echo Run the Runner with:
echo "%VENV_PYTHON%" "%CD%\ui_runner.py"
echo.
pause
exit /b 0

:python_missing
echo.
echo ERROR: Python 3 was not found.
echo Install Python 3 and enable "Add Python to PATH", then run this file again.
goto :failed

:venv_failed
echo.
echo ERROR: The .venv could not be created.
goto :failed

:install_failed
echo.
echo ERROR: Package installation failed.
echo Check the internet connection and the messages above.
goto :failed

:verify_failed
echo.
echo ERROR: Installation finished, but dependency verification failed.
echo Review the messages above.
goto :failed

:failed
echo.
pause
exit /b 1
