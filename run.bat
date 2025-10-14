@echo off
REM GammaScope Launcher for Windows
REM This ensures the correct Python environment is used

echo ========================================
echo GammaScope Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
) else (
    echo WARNING: No virtual environment found.
    echo Using system Python...
    echo.
)

REM Check Python version
python --version
echo.

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please run this script from the gamma_scope directory.
    pause
    exit /b 1
)

REM Run the application
echo Starting GammaScope...
echo.
python main.py %*

pause
