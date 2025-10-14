# GammaScope Troubleshooting Guide

## "ModuleNotFoundError: No module named 'requests'" (or other modules)

This error means Python can't find the installed packages. Here are the solutions:

### Solution 1: Use the Provided Batch Files (Windows - Easiest)

We've created helper scripts for you:

```bash
# Setup virtual environment (run once)
setup_venv.bat

# Then run in demo mode (no API needed)
run_demo.bat

# OR run in live mode (needs Alpaca credentials)
run.bat
```

These scripts ensure the correct Python environment is used.

---

### Solution 2: Create and Use a Virtual Environment (Recommended)

**Step-by-step:**

1. **Create virtual environment:**
   ```bash
   cd gamma_scope
   python -m venv venv
   ```

2. **Activate it:**

   **Windows (Command Prompt):**
   ```bash
   venv\Scripts\activate
   ```

   **Windows (PowerShell):**
   ```bash
   venv\Scripts\Activate.ps1
   ```

   **Git Bash / WSL:**
   ```bash
   source venv/Scripts/activate
   ```

3. **Verify activation** - you should see `(venv)` in your prompt:
   ```
   (venv) C:\Users\matto\projects\GEX\gamma_scope>
   ```

4. **Install packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the app:**
   ```bash
   python main.py
   ```

---

### Solution 3: Install Packages Globally (Not Recommended)

If you don't want to use a virtual environment:

```bash
cd gamma_scope
python -m pip install -r requirements.txt
```

Then run:
```bash
python main.py
```

---

### Solution 4: Check Your IDE Settings

If you're running from an IDE (VS Code, PyCharm, etc.):

#### **VS Code:**
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose the Python in `venv\Scripts\python.exe`
4. Or choose your global Python 3.13

#### **PyCharm:**
1. File → Settings → Project → Python Interpreter
2. Click gear icon → Add
3. Select "Existing environment"
4. Browse to `venv\Scripts\python.exe`

---

## Other Common Issues

### Issue: "python: command not found"

**Solution:**
- Windows: Try using `py` instead of `python`:
  ```bash
  py -m pip install -r requirements.txt
  py main.py
  ```

- Or add Python to PATH:
  1. Search for "Environment Variables" in Windows
  2. Edit PATH
  3. Add: `C:\Users\matto\AppData\Local\Programs\Python\Python313`

---

### Issue: "streamlit: command not found"

**Solution:** Always use `python -m`:
```bash
# ❌ Don't use
streamlit run src/webapp.py

# ✅ Do use
python main.py --webapp
```

---

### Issue: Port 8501 already in use

**Solution:**

**Option A - Kill existing process:**
```bash
# Windows Command Prompt
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

**Option B - Use different port:**
```bash
python -m streamlit run src/webapp.py --server.port 8502
```

---

### Issue: "Configuration error: Required environment variable X is not set"

**Solution:**

1. **Make sure `.env` file exists:**
   ```bash
   # Check if it exists
   dir .env

   # If not, copy from example
   copy .env.example .env
   ```

2. **Edit `.env` file** and add your credentials:
   ```env
   ALPACA_API_KEY=your_key_here
   ALPACA_SECRET_KEY=your_secret_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

3. **Or use demo mode** (no credentials needed):
   - Edit `config.json`
   - Set `"sample_mode": true`

---

### Issue: "No data available for symbol"

**Solution:**

1. **Wait for first refresh** - Initial data fetch takes 10-60 seconds

2. **Or manually trigger:**
   ```bash
   python main.py --once
   ```

3. **Check logs** for API errors:
   ```bash
   python main.py --debug
   ```

4. **Verify Alpaca credentials** are correct

5. **Check Alpaca API status:** https://status.alpaca.markets/

---

### Issue: "Rate limit exceeded"

**Solution:** Reduce refresh frequency in `config.json`:

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

### Issue: Database locked errors

**Solution:**

1. **Make sure only one instance is running**

2. **Reset database:**
   ```bash
   del data\cache.db
   ```

3. **Check file permissions** on `data\` folder

---

### Issue: Import errors in IDE

**Solution:**

If you see red squiggly lines or import errors in your IDE:

1. **VS Code:** Install Python extension, select correct interpreter

2. **Add to PYTHONPATH:**
   ```bash
   set PYTHONPATH=%PYTHONPATH%;C:\Users\matto\projects\GEX\gamma_scope
   ```

---

## Quick Diagnostic Commands

Run these to diagnose issues:

```bash
# 1. Check Python version (need 3.11+)
python --version

# 2. Check which Python is being used
python -c "import sys; print(sys.executable)"

# 3. Check if packages are installed
python -m pip list

# 4. Try importing each package
python -c "import requests; import pandas; import streamlit; print('All packages OK')"

# 5. Check if virtual environment is active
where python
# Should show venv\Scripts\python.exe if venv is active

# 6. Run in debug mode
python main.py --debug
```

---

## Fresh Start (Nuclear Option)

If nothing works, start completely fresh:

```bash
# 1. Delete virtual environment
rmdir /s /q venv

# 2. Delete Python cache
rmdir /s /q src\__pycache__
rmdir /s /q tests\__pycache__
del /q *.pyc

# 3. Recreate everything
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Test
python -m pytest tests/ -v

# 5. Run
python main.py
```

---

## Getting Help

### Before asking for help, please provide:

1. **Python version:**
   ```bash
   python --version
   ```

2. **OS version:**
   ```bash
   ver
   ```

3. **Installed packages:**
   ```bash
   pip list
   ```

4. **Error message** (full traceback)

5. **What you tried** (commands you ran)

6. **Screenshots** if relevant

---

## Contact & Resources

- **Alpaca API Docs:** https://docs.alpaca.markets/
- **Alpaca Status:** https://status.alpaca.markets/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Python Docs:** https://docs.python.org/3/

---

## Quick Reference: File Locations

```
Windows:
- Python: C:\Users\matto\AppData\Local\Programs\Python\Python313\
- Packages: C:\Users\matto\AppData\Local\Programs\Python\Python313\Lib\site-packages\
- Venv: C:\Users\matto\projects\GEX\gamma_scope\venv\
```

---

**Most issues are solved by using a virtual environment and ensuring it's activated!**

The easiest way: Just run `setup_venv.bat` then `run_demo.bat` 🚀
