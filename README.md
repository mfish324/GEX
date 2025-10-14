# 📊 GammaScope - Options Gamma Exposure Monitor

A comprehensive Python-based application for monitoring and analyzing Options Gamma Exposure (GEX) across multiple symbols using real-time data from Alpaca Markets API.

## 🎯 Features

- **Real-time GEX Calculation**: Compute Gamma Exposure (GEX) and Delta Exposure (DEX) for configured symbols
- **Gamma Flip Point Detection**: Automatically detect price levels where market maker positioning changes
- **Interactive Dashboard**: Streamlit-based web interface with multiple visualization options
- **Automatic Data Refresh**: Configurable periodic updates using APScheduler
- **Historical Tracking**: SQLite database for caching and historical analysis
- **Multiple Symbols**: Track SPY, SPX, QQQ, or any equity options
- **Sample Mode**: Demo mode with sample data for testing without API credentials

## 📐 GEX Formula

GammaScope uses the industry-standard formula for calculating Gamma Exposure:

```
GEX_per_option = Gamma × OpenInterest × ContractMultiplier × UnderlyingPrice × 0.01
```

Where:
- **Gamma**: The gamma Greek value from the option
- **OpenInterest**: Number of open contracts
- **ContractMultiplier**: Typically 100 for standard equity options
- **UnderlyingPrice**: Current price of the underlying asset
- **0.01**: Conversion factor for dollar terms

**Net GEX Interpretation**:
- ✅ **Positive GEX**: Market makers are long gamma → Price stabilizing effect (reduced volatility)
- ⚠️ **Negative GEX**: Market makers are short gamma → Price destabilizing effect (increased volatility)

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Alpaca Markets account (free paper trading account works)
  - Sign up at: https://app.alpaca.markets/signup

### Installation

1. **Clone or download the repository**:
   ```bash
   cd gamma_scope
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Alpaca credentials:
   ```env
   ALPACA_API_KEY=your_api_key_here
   ALPACA_SECRET_KEY=your_secret_key_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   DEBUG=false
   ```

5. **Configure tracked symbols** (optional):

   Edit `config.json` to customize tracked symbols and settings:
   ```json
   {
     "symbols": ["SPY", "QQQ", "SPX"],
     "refresh_interval_minutes": 5,
     "sample_mode": false
   }
   ```

6. **Run the application**:
   ```bash
   python main.py
   ```

7. **Access the dashboard**:

   Open your browser to: http://localhost:8501

## 🎮 Usage Modes

### Full System (Default)
Runs both the data refresh scheduler and web dashboard:
```bash
python main.py
```

### Webapp Only
Run just the web interface (requires existing data):
```bash
python main.py --webapp
```

### Scheduler Only
Run just the background data refresh (no UI):
```bash
python main.py --scheduler
```

### Single Fetch
Fetch data once and exit (useful for cron jobs or testing):
```bash
python main.py --once
```

### Demo Mode
To run with sample data (no API credentials required), set in `config.json`:
```json
{
  "sample_mode": true
}
```

Then run:
```bash
python main.py
```

## 📁 Project Structure

```
gamma_scope/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .env                    # Your credentials (create this)
├── config.json             # Application configuration
├── README.md               # This file
├── data/
│   └── cache.db            # SQLite database (auto-created)
├── src/
│   ├── __init__.py
│   ├── alpaca_client.py    # Alpaca API wrapper
│   ├── gex_calculator.py   # GEX/DEX computation engine
│   ├── models.py           # Database models (SQLAlchemy)
│   ├── scheduler.py        # APScheduler refresh jobs
│   ├── utils.py            # Config and helper functions
│   ├── visualization.py    # Plotly chart builders
│   └── webapp.py           # Streamlit dashboard
└── tests/
    └── test_gex_calculator.py  # Unit tests
```

## 📊 Dashboard Features

### Overview Tab
- Key metrics: Net GEX, Call GEX, Put GEX, Gamma Flip Point
- Interactive GEX vs Strike chart
- Toggle between net GEX and separate call/put views
- Real-time interpretation of market maker positioning

### Detailed Analysis Tab
- Cumulative GEX curve
- Open Interest distribution
- Strike-level data table
- CSV and JSON export options

### Historical Tab
- GEX timeline chart
- Underlying price correlation
- Statistical summary (mean, max, min, std dev)

### Configuration Tab
- View current settings
- Symbol configuration
- Refresh interval
- Environment info

## ⚙️ Configuration

### config.json Parameters

```json
{
  "symbols": ["SPY", "QQQ", "SPX"],           // Symbols to track
  "refresh_interval_minutes": 5,              // Data refresh frequency
  "contract_multipliers": {                   // Per-symbol multipliers
    "SPY": 100,
    "QQQ": 100,
    "SPX": 100
  },
  "ui_preferences": {
    "theme": "light",
    "default_chart_height": 600,
    "show_cumulative": true
  },
  "data_retention_days": 7,                   // Historical data retention
  "sample_mode": false,                       // Enable demo mode
  "expiration_filter": {
    "use_nearest_expiry": false,              // Filter by nearest expiration
    "days_to_expiry_min": 0,                  // Min days to expiry
    "days_to_expiry_max": 60                  // Max days to expiry
  }
}
```

### Environment Variables (.env)

```env
# Required
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Optional
DEBUG=false
```

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Individual Components

**Test GEX Calculator**:
```bash
python -m src.gex_calculator
```

**Test Alpaca Client**:
```bash
python -m src.alpaca_client
```

**Test Database**:
```bash
python -m src.models
```

## 🔧 Troubleshooting

### "Configuration error: Required environment variable not set"
- Ensure `.env` file exists and contains all required variables
- Check that you've copied `.env.example` to `.env`
- Verify your Alpaca API credentials are correct

### "No data available for symbol"
- Check that data refresh has completed at least once
- Verify your Alpaca account has access to options data
- Try running `python main.py --once` to fetch data manually
- Check logs for API errors

### "Streamlit not found"
- Ensure you've installed all requirements: `pip install -r requirements.txt`
- Try reinstalling: `pip install --upgrade streamlit`

### Rate Limiting / API Errors
- The client implements automatic retry logic and rate limiting
- Reduce refresh frequency in `config.json` if hitting limits
- Consider using `expiration_filter.use_nearest_expiry: true` to reduce API calls

### Database Locked Errors
- Ensure only one instance of the scheduler is running
- Check file permissions on `data/cache.db`
- Delete `data/cache.db` to reset (will lose historical data)

## 📚 API Documentation

### Alpaca Options API
This application uses Alpaca's Options API (v2beta1):
- Documentation: https://docs.alpaca.markets/docs/options-trading
- Endpoint: `/v2beta1/options`
- Rate Limits: 200 requests/minute for most endpoints

### Key Endpoints Used
- `GET /v2/stocks/{symbol}/snapshot` - Underlying price
- `GET /v2/options/contracts` - Option chain
- `GET /v2/options/snapshots` - Options data with Greeks

## 🎓 Understanding GEX

### What is Gamma Exposure?

Gamma Exposure (GEX) represents the sensitivity of option dealers' delta hedges to changes in the underlying asset price. It's a key metric for understanding:

1. **Market Structure**: How market makers' hedging activity affects price action
2. **Volatility Regime**: Whether volatility is likely to increase or decrease
3. **Support/Resistance**: Price levels with significant option positioning

### Gamma Flip Point

The **gamma flip point** is the price level where net GEX changes from positive to negative (or vice versa). This is significant because:

- **Above flip point**: Positive GEX → Dealers stabilize prices by selling rallies
- **Below flip point**: Negative GEX → Dealers amplify moves by buying rallies

### Practical Applications

1. **Volatility Forecasting**: Negative GEX often precedes volatility expansion
2. **Support/Resistance**: Large GEX concentrations can act as price magnets
3. **Risk Management**: Understanding dealer positioning helps with trade timing
4. **Market Regime**: Identify whether you're in a range-bound or trending environment

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional chart types and visualizations
- More sophisticated expiration filtering
- Real-time WebSocket updates
- Additional Greeks analysis (Vanna, Charm, etc.)
- Machine learning for GEX-based predictions
- Export to additional formats (Excel, PDF)

## ⚠️ Disclaimer

This software is for educational and informational purposes only. It is not financial advice. Options trading involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results.

The authors and contributors are not responsible for any financial losses incurred through the use of this software.

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Alpaca Markets** for providing options data API
- **Streamlit** for the excellent web framework
- **Plotly** for interactive visualizations
- Options trading community for GEX methodology

## 📞 Support

For issues and questions:
- Check the Troubleshooting section above
- Review Alpaca API documentation
- Open an issue on GitHub (if applicable)

---

**Built with ❤️ for options traders and quants**

*Last updated: 2025*
