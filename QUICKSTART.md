# GammaScope - Quick Start Guide

Get GammaScope up and running in 5 minutes!

## 🚀 Fast Setup

### Option 1: Automated Setup (Recommended)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Run setup wizard
python setup.py
```

The setup wizard will guide you through:
- Installing dependencies
- Configuring API credentials
- Setting up your environment

### Option 2: Manual Setup

```bash
# 1. Create and activate venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure .env
cp .env.example .env
# Edit .env with your Alpaca credentials

# 4. Run the app
python main.py
```

## 🎮 Running GammaScope

### Demo Mode (No API Required)

Perfect for testing and learning how GammaScope works:

1. Edit `config.json`:
   ```json
   {
     "sample_mode": true
   }
   ```

2. Run:
   ```bash
   python main.py
   ```

3. Open http://localhost:8501

### Live Mode (With Alpaca API)

1. Get Alpaca API credentials:
   - Sign up at https://app.alpaca.markets/signup
   - Use paper trading (free) or live account
   - Copy your API Key and Secret

2. Configure `.env`:
   ```env
   ALPACA_API_KEY=your_key_here
   ALPACA_SECRET_KEY=your_secret_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

3. Set `config.json`:
   ```json
   {
     "sample_mode": false,
     "symbols": ["SPY", "QQQ"],
     "refresh_interval_minutes": 5
   }
   ```

4. Run:
   ```bash
   python main.py
   ```

## 📊 Using the Dashboard

Once running, navigate to http://localhost:8501

### Overview Tab
- View current GEX metrics for selected symbol
- See gamma flip point and net positioning
- Interactive strike distribution chart

### Detailed Analysis Tab
- Per-strike breakdown table
- Cumulative GEX curve
- Open interest distribution
- Export data as CSV or JSON

### Historical Tab
- View GEX evolution over time
- Correlation with underlying price
- Statistical summary

## 🔧 Common Commands

```bash
# Full system (scheduler + webapp)
python main.py

# Webapp only (faster startup, requires existing data)
python main.py --webapp

# Scheduler only (background data collection)
python main.py --scheduler

# Fetch data once and exit
python main.py --once

# Run with debug logging
python main.py --debug

# Run tests
pytest tests/ -v
```

## 💡 Tips

### First Time Setup
1. Start with demo mode to understand the interface
2. Switch to live mode with paper trading
3. Monitor a single symbol (SPY) first
4. Gradually add more symbols

### Performance
- Use `expiration_filter` in config.json to reduce API calls
- Start with longer refresh intervals (15-30 minutes)
- Monitor API rate limits in logs

### Data Management
- Historical data is stored in `data/cache.db`
- Adjust `data_retention_days` to control database size
- Export important data regularly

## ❓ Troubleshooting

### "No data available"
```bash
# Manually trigger a data fetch
python main.py --once
```

### "Configuration error"
```bash
# Verify your .env file exists and has valid credentials
cat .env  # Linux/Mac
type .env  # Windows
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port 8501 already in use
```bash
# Kill existing Streamlit processes
# Windows:
taskkill /F /IM streamlit.exe
# Linux/Mac:
pkill -f streamlit
```

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [config.json](config.json) for all available options
- Check out the code in [src/](src/) to understand internals
- Customize visualizations in [src/visualization.py](src/visualization.py)

## 🆘 Getting Help

1. Check the logs in the console output
2. Review the [README.md](README.md) troubleshooting section
3. Verify Alpaca API status: https://status.alpaca.markets/
4. Test with demo mode to isolate issues

---

**Ready to monitor gamma exposure! 📊🚀**
