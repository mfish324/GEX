@echo off
REM Setup virtual environment for GammaScope

echo ========================================
echo GammaScope Virtual Environment Setup
echo ========================================
echo.

REM Check if venv already exists
if exist "venv\" (
    echo Virtual environment already exists.
    choice /C YN /M "Do you want to recreate it"
    if errorlevel 2 goto :skip_create
    if errorlevel 1 (
        echo Removing old virtual environment...
        rmdir /s /q venv
    )
)

:create_venv
echo.
echo Creating virtual environment...
python -m venv venv

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create virtual environment!
    echo Make sure Python 3.11+ is installed and in your PATH.
    pause
    exit /b 1
)

echo Virtual environment created successfully!

:skip_create
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Some packages failed to install!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Virtual environment created and packages installed.
echo.
echo Next steps:
echo 1. Edit .env file with your Alpaca credentials
echo 2. Run: run_demo.bat (for demo mode)
echo    OR:  run.bat (for live mode)
echo.
pause
