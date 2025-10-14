# GammaScope - Usage Examples

This guide provides practical examples of using GammaScope for options gamma exposure analysis.

## 🎯 Example 1: Basic Usage - SPY Analysis

### Step 1: Configure for SPY monitoring

Edit `config.json`:
```json
{
  "symbols": ["SPY"],
  "refresh_interval_minutes": 5,
  "sample_mode": false
}
```

### Step 2: Run the application
```bash
python main.py
```

### Step 3: View Results
Navigate to http://localhost:8501

**Expected Output:**
- Net GEX: e.g., +$1.2B (positive = long gamma)
- Call GEX: e.g., +$2.1B
- Put GEX: e.g., $850M
- Gamma Flip: e.g., $448.50

**Interpretation:**
If Net GEX is +$1.2B, market makers are long gamma, which suggests:
- Price stabilization (dealers sell rallies, buy dips)
- Reduced volatility expected
- Underlying likely to stay range-bound

---

## 🎯 Example 2: Multi-Symbol Comparison

### Monitor SPY, QQQ, and IWM simultaneously

`config.json`:
```json
{
  "symbols": ["SPY", "QQQ", "IWM"],
  "refresh_interval_minutes": 10
}
```

### Sample Results Dashboard View:

| Symbol | Price   | Net GEX    | Call GEX   | Put GEX   | Flip Point | Status        |
|--------|---------|------------|------------|-----------|------------|---------------|
| SPY    | $450.25 | +$1.25B    | +$2.10B    | $850M     | $448.50    | 🟢 Long Gamma |
| QQQ    | $380.75 | -$350M     | +$450M     | $800M     | $382.25    | 🔴 Short Gamma|
| IWM    | $195.50 | +$125M     | +$280M     | $155M     | $194.80    | 🟢 Long Gamma |

**Analysis:**
- SPY: Strong long gamma positioning → expect low volatility
- QQQ: Short gamma → potential for increased volatility
- IWM: Moderate long gamma → some stabilization

---

## 🎯 Example 3: Gamma Flip Analysis

### Scenario: SPY at $450, Flip Point at $448.50

**Above Flip ($450 > $448.50):**
- Net GEX: Positive (+$1.2B)
- Market Maker Position: Long Gamma
- Hedging Behavior: Sell rallies, buy dips
- Effect: Price stabilization
- Volatility: Suppressed

**Below Flip (if price drops to $448):**
- Net GEX: Negative
- Market Maker Position: Short Gamma
- Hedging Behavior: Buy rallies, sell dips
- Effect: Price amplification
- Volatility: Elevated

**Trading Implications:**
- **At $450**: Mean reversion strategies favored
- **Below $448.50**: Trend-following strategies favored
- **Near $448.50**: High volatility potential

---

## 🎯 Example 4: Historical Analysis

### Tracking GEX Changes Over Time

Run for 1 week, then view Historical tab:

**Sample Timeline Data:**
```
Date/Time           | Net GEX    | Price   | Change
--------------------|------------|---------|--------
2025-01-20 09:30    | +$1.50B    | $451.20 | --
2025-01-20 14:00    | +$1.35B    | $450.80 | -10%
2025-01-21 09:30    | +$800M     | $449.50 | -40%
2025-01-21 14:00    | -$200M     | $447.20 | FLIP!
2025-01-22 09:30    | -$450M     | $445.80 | -125%
```

**Observations:**
1. Day 1: Stable positive GEX, price stable
2. Day 2 AM: GEX declining, price drifting lower
3. Day 2 PM: **Gamma flip occurred**, price accelerated down
4. Day 3: Negative GEX, increased volatility

**Lesson:** Gamma flip often precedes volatility expansion

---

## 🎯 Example 5: Strike-Level Analysis

### Detailed Per-Strike Breakdown

**Example Data for SPY:**

| Strike | Call GEX  | Put GEX   | Net GEX   | Call OI | Put OI | Total OI |
|--------|-----------|-----------|-----------|---------|--------|----------|
| $440   | +$150M    | $80M      | +$70M     | 15,000  | 8,000  | 23,000   |
| $445   | +$350M    | $180M     | +$170M    | 35,000  | 18,000 | 53,000   |
| $450   | +$800M    | $400M     | +$400M    | 80,000  | 45,000 | 125,000  |
| $455   | +$600M    | $150M     | +$450M    | 60,000  | 15,000 | 75,000   |
| $460   | +$200M    | $40M      | +$160M    | 20,000  | 4,000  | 24,000   |

**Key Insights:**
- **$450 Strike**: Highest concentration (125K OI)
  - Acts as price magnet
  - Likely support/resistance level
- **$455 Strike**: Highest net GEX (+$450M)
  - Strong dealer long gamma above current price
- **Distribution**: Call-heavy above current, balanced below

---

## 🎯 Example 6: Export and External Analysis

### Export Data for Further Analysis

1. **CSV Export** (from Detailed Analysis tab):
```csv
Strike,Call GEX,Put GEX,Net GEX,Call OI,Put OI,Total OI
440,150000000,80000000,70000000,15000,8000,23000
445,350000000,180000000,170000000,35000,18000,53000
...
```

2. **JSON Export**:
```json
{
  "symbol": "SPY",
  "timestamp": "2025-01-20T14:30:00",
  "underlying_price": 450.25,
  "net_gex": 1250000000,
  "total_call_gex": 2100000000,
  "total_put_gex": 850000000,
  "gamma_flip_point": 448.50,
  "per_strike": { ... }
}
```

3. **Use Cases for Exported Data:**
   - Import into Excel/Google Sheets
   - Feed into trading algorithms
   - Create custom visualizations in Python/R
   - Historical backtesting
   - Risk management calculations

---

## 🎯 Example 7: Real-Time Monitoring Setup

### Optimized Configuration for Active Trading

`config.json`:
```json
{
  "symbols": ["SPY"],
  "refresh_interval_minutes": 5,
  "expiration_filter": {
    "use_nearest_expiry": true,
    "days_to_expiry_min": 0,
    "days_to_expiry_max": 7
  },
  "data_retention_days": 30
}
```

**Benefits:**
- **5-minute refresh**: Near real-time monitoring
- **Nearest expiry only**: Reduces API calls, focuses on most liquid contracts
- **0-7 days**: Weekly options only (high gamma, most impact)
- **30-day retention**: Month of historical data

### Monitoring Workflow:

```bash
# Terminal 1: Run scheduler only
python main.py --scheduler

# Terminal 2: Run webapp only (faster startup)
python main.py --webapp

# Or combined:
python main.py
```

### Dashboard Usage:
1. **Pre-Market (8:00 AM)**: Check overnight GEX changes
2. **Market Open (9:30 AM)**: Monitor flip point vs price
3. **Intraday**: Watch for significant GEX shifts
4. **Market Close (4:00 PM)**: Review daily changes

---

## 🎯 Example 8: Demo Mode for Learning

### Perfect for Understanding GEX Without API

1. **Enable Demo Mode** (`config.json`):
```json
{
  "sample_mode": true,
  "symbols": ["SPY", "QQQ"]
}
```

2. **Run:**
```bash
python main.py
```

3. **Explore:**
   - Toggle between Overview/Analysis/Historical tabs
   - Switch between Call/Put separate views
   - Export sample data
   - Understand the interface

**No API credentials required!**

---

## 🎯 Example 9: Command-Line Quick Checks

### Fetch Data Without Starting UI

```bash
# One-time data fetch
python main.py --once

# View results programmatically
python -c "
from src.models import DatabaseManager
from src.utils import format_large_number

db = DatabaseManager()
snap = db.get_latest_snapshot('SPY')

if snap:
    print(f'SPY @ \${snap.underlying_price:.2f}')
    print(f'Net GEX: {format_large_number(snap.net_gex)}')
    print(f'Flip: \${snap.gamma_flip_point:.2f}')
"
```

---

## 🎯 Example 10: Automated Alerts (Custom)

### Extend GammaScope with Alert Logic

Create `alerts.py`:
```python
from src.models import DatabaseManager
from src.utils import Config

def check_gamma_flip_alert(symbol, threshold=0.02):
    """Alert if price is within 2% of flip point"""
    db = DatabaseManager()
    snap = db.get_latest_snapshot(symbol)

    if snap and snap.gamma_flip_point:
        price = snap.underlying_price
        flip = snap.gamma_flip_point
        pct_diff = abs(price - flip) / flip

        if pct_diff < threshold:
            print(f"🚨 ALERT: {symbol} near gamma flip!")
            print(f"   Price: ${price:.2f}")
            print(f"   Flip:  ${flip:.2f}")
            print(f"   Diff:  {pct_diff*100:.1f}%")
            return True

    return False

# Run check
if __name__ == '__main__':
    config = Config()
    for symbol in config.symbols:
        check_gamma_flip_alert(symbol)
```

Run periodically:
```bash
# Check every 5 minutes
python alerts.py
```

---

## 📊 Interpreting Common GEX Scenarios

### Scenario 1: Large Positive GEX
- **Net GEX**: > +$1B
- **Implication**: Strong dealer long gamma
- **Expected**: Low volatility, range-bound price
- **Strategy**: Sell options, mean reversion trades

### Scenario 2: Large Negative GEX
- **Net GEX**: < -$1B
- **Implication**: Dealers short gamma
- **Expected**: High volatility, potential trending
- **Strategy**: Buy options, trend-following

### Scenario 3: Near Zero GEX
- **Net GEX**: -$200M to +$200M
- **Implication**: Balanced positioning
- **Expected**: Unpredictable, breakout potential
- **Strategy**: Wait for direction confirmation

### Scenario 4: Rapidly Decreasing GEX
- **Change**: -50% in one day
- **Implication**: Positioning shift, risk-off
- **Expected**: Volatility expansion likely
- **Strategy**: Increase caution, reduce size

---

## 🎓 Best Practices

1. **Monitor Flip Point Daily**: Track changes vs underlying
2. **Compare Multiple Symbols**: Relative GEX shows sector trends
3. **Historical Context**: Compare to recent averages
4. **Combine with TA**: Use GEX for context, not signals
5. **Track Changes**: Absolute values less important than trends
6. **Consider Expiration**: Near-term expirations have most impact

---

## 🔗 Integration Examples

### With Trading Journal:
```bash
python main.py --once
# Export JSON, append to journal
```

### With Discord/Slack:
```python
# Post daily GEX summary to Discord webhook
import requests
summary = f"SPY GEX: {net_gex}, Flip: {flip}"
requests.post(webhook_url, json={"content": summary})
```

### With Cron (Linux):
```bash
# Fetch data every 15 minutes during market hours
*/15 9-16 * * 1-5 cd /path/to/gamma_scope && python main.py --once
```

---

**These examples demonstrate the versatility of GammaScope for options analysis!**

For more advanced usage, see [README.md](README.md) and explore the source code in [src/](src/).
