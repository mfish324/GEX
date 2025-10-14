# GammaScope - Installation Guide

## Step-by-Step Installation

### Step 1: Verify Python Installation

```bash
python --version
```

**Required:** Python 3.11 or higher

If you need to install Python:
- Windows: Download from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

---

### Step 2: Create Virtual Environment

Navigate to the gamma_scope directory:

```bash
cd gamma_scope
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

---

### Step 3: Install Dependencies

**Option A: Install all at once (recommended)**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Option B: If you encounter errors, install individually:**

```bash
pip install --upgrade pip
pip install python-dotenv
pip install requests
pip install pandas numpy
pip install alpaca-py
pip install sqlalchemy
pip install apscheduler
pip install plotly matplotlib
pip install streamlit
pip install pytest pytest-cov
```

---

### Step 4: Configure Environment

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Edit `.env` with your text editor and add your Alpaca credentials:

```env
ALPACA_API_KEY=PK...your_key_here
ALPACA_SECRET_KEY=...your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
DEBUG=false
```

**To get Alpaca credentials:**
1. Sign up at https://app.alpaca.markets/signup
2. Use paper trading (free) for testing
3. Go to Dashboard → API Keys
4. Generate new API key

---

### Step 5: Test the Installation

**Test 1: Run in demo mode (no API required)**

Edit `config.json` and set:
```json
{
  "sample_mode": true
}
```

Then run:
```bash
python main.py
```

You should see:
```
GammaScope - Options Gamma Exposure Monitor
============================================================
Tracking symbols: SPY, QQQ, SPX
Sample mode: ON
...
Starting webapp...
```

**Test 2: Run unit tests**

```bash
pytest tests/ -v
```

All tests should pass.

---

### Step 6: Run with Live Data

Edit `config.json` and set:
```json
{
  "sample_mode": false,
  "symbols": ["SPY"],
  "refresh_interval_minutes": 5
}
```

Run the application:
```bash
python main.py
```

Wait for initial data fetch to complete, then open your browser to:
```
http://localhost:8501
```

---

## Common Installation Issues

### Issue 1: "python: command not found"
**Solution:**
- Windows: Use `py` instead of `python`
- Or add Python to your PATH
- Reinstall Python with "Add to PATH" checked

### Issue 2: "pip: command not found"
**Solution:**
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Issue 3: "alpaca-py installation failed"
**Solution:** Install dependencies first:
```bash
pip install setuptools wheel
pip install alpaca-py
```

### Issue 4: "Microsoft Visual C++ required" (Windows)
**Solution:** Install Microsoft C++ Build Tools
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Or install lighter dependencies:
```bash
pip install --only-binary :all: alpaca-py
```

### Issue 5: "Streamlit not starting"
**Solution:**
```bash
# Reinstall streamlit
pip uninstall streamlit
pip install streamlit

# Or specify port manually
streamlit run src/webapp.py --server.port 8502
```

### Issue 6: "sqlite3.OperationalError: unable to open database file"
**Solution:**
```bash
# Create data directory
mkdir data

# Check permissions
# Windows: Right-click data folder → Properties → Security
# Linux/Mac: chmod 755 data
```

### Issue 7: "Rate limit exceeded" from Alpaca
**Solution:** Edit `config.json`:
```json
{
  "refresh_interval_minutes": 15,
  "expiration_filter": {
    "use_nearest_expiry": true,
    "days_to_expiry_max": 7
  }
}
```

---

## Verification Checklist

After installation, verify:

- [ ] Virtual environment is activated (you see `(venv)` in prompt)
- [ ] All packages installed without errors: `pip list`
- [ ] `.env` file exists and has your credentials
- [ ] `config.json` exists
- [ ] Demo mode works: `python main.py` with `sample_mode: true`
- [ ] Unit tests pass: `pytest tests/ -v`
- [ ] Dashboard opens at http://localhost:8501

---

## Quick Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install/update dependencies
pip install -r requirements.txt

# Run application
python main.py                 # Full system
python main.py --webapp        # UI only
python main.py --scheduler     # Data collection only
python main.py --once          # Single fetch
python main.py --debug         # Debug mode

# Run tests
pytest tests/ -v

# Deactivate virtual environment
deactivate
```

---

## Alternative: Minimal Installation

If you just want to test the core functionality without the full dashboard:

```bash
# Install only core dependencies
pip install python-dotenv requests pandas numpy alpaca-py

# Test GEX calculator
python -m src.gex_calculator

# Test Alpaca client
python -m src.alpaca_client
```

---

## Next Steps After Installation

1. **Start with demo mode** to learn the interface
2. **Configure your symbols** in `config.json`
3. **Set up Alpaca credentials** for live data
4. **Explore the dashboard** at http://localhost:8501
5. **Read EXAMPLES.md** for usage scenarios

---

## Getting Help

If you're still having issues:

1. Check Python version: `python --version` (must be 3.11+)
2. Check if venv is activated: look for `(venv)` in prompt
3. Check installed packages: `pip list`
4. Run in debug mode: `python main.py --debug`
5. Check the logs for specific error messages
6. Try demo mode first to isolate API-related issues

---

**You're ready to start monitoring gamma exposure!** 📊
