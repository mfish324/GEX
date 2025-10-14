@echo off
REM Quick launcher for GammaScope in DEMO MODE
REM No API credentials required!

echo ========================================
echo GammaScope - DEMO MODE
echo ========================================
echo.
echo This will run GammaScope with sample data.
echo No Alpaca API credentials needed!
echo.

REM Ensure sample mode is enabled
python -c "import json; config = json.load(open('config.json')); config['sample_mode'] = True; json.dump(config, open('config.json', 'w'), indent=2)"

echo Sample mode enabled in config.json
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the application
echo Starting GammaScope in demo mode...
echo.
echo Once started, open your browser to:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the application.
echo.

python main.py

pause
