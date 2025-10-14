# Using GammaScope with Your Existing "GEX" Virtual Environment

## ✅ Good News!

Your existing "GEX" virtual environment already has all the required packages installed and everything is working correctly!

---

## 🚀 How to Run GammaScope

Since you're already in your GEX virtual environment, you can run GammaScope directly:

### **Option 1: Demo Mode (Recommended to Start)**

```bash
# Make sure you're in the gamma_scope directory
cd gamma_scope

# Run the application
python main.py
```

Then open your browser to: **http://localhost:8501**

You'll see the dashboard with sample data for SPY and QQQ!

---

### **Option 2: Live Data Mode**

If you want to use real Alpaca data:

1. **Add your Alpaca credentials to `.env`** (you have this file open):
   ```env
   ALPACA_API_KEY=PK...your_key_here
   ALPACA_SECRET_KEY=...your_secret_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

2. **Edit `config.json`** and change:
   ```json
   {
     "sample_mode": false
   }
   ```

3. **Run:**
   ```bash
   python main.py
   ```

---

## 🔧 Verifying Your Environment

You can always check that everything is working:

```bash
# Verify all packages are installed
python check_installation.py

# Run unit tests
python -m pytest tests/ -v
```

---

## 📝 Common Commands

```bash
# Full system (scheduler + webapp)
python main.py

# Webapp only (faster startup)
python main.py --webapp

# Scheduler only (background data collection)
python main.py --scheduler

# Fetch data once and exit
python main.py --once

# Debug mode
python main.py --debug
```

---

## 🎯 What's in Your Environment

Your GEX virtual environment already includes:
- ✅ python-dotenv
- ✅ requests
- ✅ pandas, numpy
- ✅ alpaca-py (Alpaca API client)
- ✅ sqlalchemy (database)
- ✅ apscheduler (scheduling)
- ✅ plotly, matplotlib (charts)
- ✅ streamlit (web dashboard)
- ✅ pytest (testing)

**Plus many more packages!** (backtrader, jupyter, etc.)

---

## 💡 Tips for Your Setup

### Always Activate Your GEX Environment First

If you open a new terminal:

```bash
# Activate your GEX environment
# (The exact command depends on how you created it)

# Then navigate to gamma_scope
cd C:\Users\matto\projects\GEX\gamma_scope

# Now you can run the app
python main.py
```

### Using VS Code or PyCharm

Make sure your IDE is configured to use your GEX Python interpreter:

**VS Code:**
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose your GEX environment

**PyCharm:**
1. File → Settings → Project → Python Interpreter
2. Select your GEX environment

---

## 🎨 Current Configuration

Based on your files:
- **Mode:** Sample Mode (demo data)
- **Symbols:** SPY, QQQ, SPX
- **Refresh Interval:** 5 minutes
- **.env file:** Exists
- **config.json:** Configured

---

## 🚀 Quick Start NOW

Since everything is already set up:

```bash
python main.py
```

That's it! The dashboard will open at http://localhost:8501

---

## 📊 What You'll See

The dashboard has 4 tabs:

1. **Overview**:
   - Net GEX metrics
   - Current gamma flip point
   - Interactive GEX vs Strike chart
   - Market interpretation

2. **Detailed Analysis**:
   - Cumulative GEX curves
   - Per-strike data table
   - Open interest distribution
   - Export to CSV/JSON

3. **Historical**:
   - GEX timeline
   - Price correlation
   - Statistics

4. **Configuration**:
   - Current settings
   - Symbol list
   - Refresh interval

---

## ❓ Need Help?

If you encounter issues:

```bash
# Check installation
python check_installation.py

# Run tests
python -m pytest tests/ -v

# Run in debug mode
python main.py --debug

# See troubleshooting guide
# Open TROUBLESHOOTING.md
```

---

## 🎉 You're Ready!

Your GEX environment is perfectly set up. Just run:

```bash
python main.py
```

And start monitoring options gamma exposure! 📊🚀
