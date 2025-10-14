# Setting Up GammaScope with Polygon.io

## ✅ Why Polygon.io?

Polygon.io provides **real options data with Greeks** unlike Alpaca's paper trading account:

- ✅ **Free tier available** (5 API calls/minute)
- ✅ **Options Greeks** (gamma, delta, theta, vega)
- ✅ **Open interest** data
- ✅ **Real-time and historical** data
- ✅ **No account funding required**

**Cost**: Free tier perfect for testing, $29/month for Starter plan with better limits

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Get Your Polygon.io API Key

1. Go to **https://polygon.io/**
2. Click **"Sign Up Free"**
3. Create your account
4. Go to **Dashboard → API Keys**
5. Copy your API key (starts with a long string)

### Step 2: Update Your `.env` File

Edit `gamma_scope/.env` and add:

```env
# Data Provider Selection
DATA_PROVIDER=polygon

# Polygon.io API Key
POLYGON_API_KEY=your_api_key_here_from_step_1
```

### Step 3: Update config.json

Edit `config.json`:

```json
{
  "sample_mode": false,
  "symbols": ["SPY"],
  "refresh_interval_minutes": 15
}
```

**Important**: Set refresh to 15+ minutes for free tier (5 calls/min limit)

### Step 4: Test the Connection

```bash
cd gamma_scope
python src/polygon_client.py
```

You should see:
```
SPY Price: $664.xx
Nearest SPY expiration: 2025-XX-XX
Found XXX options
```

### Step 5: Run GammaScope

```bash
python main.py
```

Then open: **http://localhost:8501**

---

## 📊 Understanding Polygon.io Rate Limits

### Free Tier (5 API calls/minute)

Each symbol refresh uses approximately:
- 1 call: Get underlying price
- 1 call: Get nearest expiration
- 1-2 calls: Get options snapshot (depends on pagination)

**Total: ~3-4 calls per symbol**

**Recommendation for free tier**:
- Track 1 symbol (SPY or QQQ)
- Set refresh interval to 15-30 minutes
- Use `use_nearest_expiry: true` to reduce calls

### Starter Plan ($29/month)

- 100 API calls/minute
- Can track multiple symbols
- Faster refresh rates (5 minutes)

### Developer Plan ($99/month)

- 1000 API calls/minute
- Real-time streaming
- Multiple symbols, fast updates

---

## ⚙️ Optimal Configuration

### For Free Tier (Recommended)

Edit `config.json`:

```json
{
  "sample_mode": false,
  "symbols": ["SPY"],
  "refresh_interval_minutes": 15,
  "expiration_filter": {
    "use_nearest_expiry": true,
    "days_to_expiry_min": 0,
    "days_to_expiry_max": 30
  }
}
```

This configuration:
- Tracks one symbol (SPY)
- Refreshes every 15 minutes (well within rate limit)
- Uses nearest expiration only (reduces API calls)
- Stays well under the 5 calls/minute limit

### For Paid Plans

```json
{
  "sample_mode": false,
  "symbols": ["SPY", "QQQ", "IWM"],
  "refresh_interval_minutes": 5,
  "expiration_filter": {
    "use_nearest_expiry": false,
    "days_to_expiry_min": 0,
    "days_to_expiry_max": 60
  }
}
```

---

## 🧪 Testing Your Setup

### Test 1: Verify API Key

```bash
python -c "from src.polygon_client import PolygonClient; import os; from dotenv import load_dotenv; load_dotenv(); client = PolygonClient(os.getenv('POLYGON_API_KEY')); print(f'SPY: ${client.get_underlying_price(\"SPY\"):.2f}')"
```

### Test 2: Full Integration Test

Create `test_polygon_integration.py`:

```python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / 'src'))

load_dotenv()

from src.polygon_client import PolygonClient
from src.gex_calculator import analyze_symbol_gex
from src.models import DatabaseManager

# Initialize
client = PolygonClient(os.getenv('POLYGON_API_KEY'))
db = DatabaseManager()

# Fetch SPY data
print("Fetching SPY data...")
spy_price = client.get_underlying_price('SPY')
print(f"SPY Price: ${spy_price:.2f}")

nearest_exp = client.get_nearest_expiration('SPY', max_days=30)
print(f"Nearest expiration: {nearest_exp}")

options = client.get_options_snapshot('SPY', expiration=nearest_exp)
print(f"Retrieved {len(options)} options")

# Calculate GEX
result = analyze_symbol_gex('SPY', options, spy_price)
print(f"\nNet GEX: ${result.net_gex:,.0f}")
print(f"Gamma Flip: ${result.gamma_flip_point:.2f}")

# Save to database
db.save_gex_snapshot(result)
print("\n✓ Data saved to database!")
```

Run it:
```bash
python test_polygon_integration.py
```

---

## 🎯 Expected Results

After setup, you should see:

**In Terminal:**
```
2025-10-14 13:00:00 - GammaScope - INFO - Polygon.io client initialized
2025-10-14 13:00:05 - GammaScope - INFO - Got underlying price for SPY: $664.82
2025-10-14 13:00:10 - GammaScope - INFO - Retrieved 287 options for SPY
2025-10-14 13:00:12 - GammaScope - INFO - GEX calculation complete for SPY: Net GEX=1,250,000,000
2025-10-14 13:00:12 - GammaScope - INFO - Data saved to database
```

**In Dashboard:**
- Real SPY price (current market price)
- Actual GEX values calculated from live options
- Real gamma flip point
- Interactive charts with live data

---

## 🔧 Troubleshooting

### "Rate limit exceeded"

**Solution**: Increase refresh interval

```json
{
  "refresh_interval_minutes": 30
}
```

### "Invalid API key"

**Solution**:
1. Check your `.env` file has correct key
2. Verify key is active in Polygon dashboard
3. Try copying key again (no extra spaces)

### "No options data returned"

**Possible causes**:
1. Market is closed (options data only during market hours 9:30-4pm ET)
2. Symbol doesn't have options
3. Network/firewall issue

**Try**:
```bash
# Test with a simple call
curl "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/SPY?apiKey=YOUR_KEY"
```

### "Taking too long to load"

**Causes**:
- Free tier rate limiting (12 seconds between calls)
- Too many options to fetch

**Solutions**:
1. Enable `use_nearest_expiry: true`
2. Be patient - first load takes 1-2 minutes
3. Use sample mode while waiting: `"sample_mode": true`

---

## 💡 Pro Tips

### Tip 1: Test with Sample Mode First

Before fetching live data, test the dashboard:
```json
{
  "sample_mode": true
}
```

Then switch to live data once familiar with the interface.

### Tip 2: Monitor API Usage

Check your usage in Polygon.io Dashboard:
- https://polygon.io/dashboard/api-keys

### Tip 3: Optimal Symbol Choice

Start with **SPY** (most liquid):
- Most options data
- Best Greeks accuracy
- Fastest API responses

### Tip 4: Schedule Updates Wisely

For free tier, run manual updates:
```bash
python main.py --once
```

Then view in dashboard without scheduler running.

### Tip 5: Upgrade When Ready

If you need:
- Multiple symbols
- Faster refreshes
- More frequent updates

Consider upgrading to **Starter plan ($29/mo)** with 100 calls/minute.

---

## 📊 Comparison: Sample vs Live Data

| Feature | Sample Mode | Polygon Live |
|---------|-------------|--------------|
| Cost | Free | Free tier available |
| Data freshness | Static | Real-time |
| Symbols | Pre-loaded (SPY, QQQ) | Any optionable symbol |
| GEX accuracy | Example values | Live market data |
| Market hours | Always available | 9:30am-4pm ET |
| Learning | ✓ Perfect | ✓ Real experience |
| Trading decisions | ✗ Not recommended | ✓ Actual data |

---

## 🎓 Next Steps

1. **✓ Get API key** from Polygon.io
2. **✓ Update `.env`** with your key
3. **✓ Set config** for free tier limits
4. **✓ Test connection** with test script
5. **✓ Run GammaScope** and see live data!
6. **Monitor usage** in Polygon dashboard
7. **Upgrade plan** if needed for more symbols/faster updates

---

## 📞 Support

- **Polygon.io Docs**: https://polygon.io/docs/options
- **Polygon.io Support**: support@polygon.io
- **Rate Limits**: https://polygon.io/pricing
- **Status**: https://status.polygon.io/

---

**You're ready to use GammaScope with real options data!** 📊🚀

Just add your Polygon API key to `.env` and run `python main.py`!
