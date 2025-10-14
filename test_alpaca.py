"""
Test Alpaca API Connection and Options Data Retrieval

This script tests:
1. Loading credentials from .env
2. Connecting to Alpaca API
3. Fetching SPY underlying price
4. Fetching SPY options data
5. Displaying sample options with Greeks
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 70)
print("Alpaca API Connection Test - SPY Options")
print("=" * 70)
print()

# Step 1: Load credentials
print("Step 1: Loading credentials from .env...")
try:
    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL')

    if not api_key or not secret_key:
        print("[ERROR] Missing credentials in .env file!")
        print("Please ensure .env contains:")
        print("  ALPACA_API_KEY=...")
        print("  ALPACA_SECRET_KEY=...")
        print("  ALPACA_BASE_URL=...")
        sys.exit(1)

    print(f"[OK] API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"[OK] Base URL: {base_url}")
    print()

except Exception as e:
    print(f"[ERROR] Failed to load credentials: {e}")
    sys.exit(1)

# Step 2: Initialize Alpaca client
print("Step 2: Initializing Alpaca client...")
try:
    from src.alpaca_client import AlpacaClient

    client = AlpacaClient(
        api_key=api_key,
        secret_key=secret_key,
        base_url=base_url
    )
    print("[OK] Alpaca client initialized")
    print()

except Exception as e:
    print(f"[ERROR] Failed to initialize client: {e}")
    sys.exit(1)

# Step 3: Get SPY underlying price
print("Step 3: Fetching SPY underlying price...")
try:
    spy_price = client.get_underlying_price('SPY')
    print(f"[OK] SPY Current Price: ${spy_price:.2f}")
    print()

except Exception as e:
    print(f"[ERROR] Failed to get SPY price: {e}")
    print()
    print("Possible issues:")
    print("  - Invalid API credentials")
    print("  - No market data subscription")
    print("  - API endpoint changed")
    print("  - Network/firewall issue")
    print()
    print("Check your credentials at: https://app.alpaca.markets/paper/dashboard/overview")
    sys.exit(1)

# Step 4: Find nearest expiration
print("Step 4: Finding nearest SPY options expiration...")
try:
    nearest_exp = client.get_nearest_expiration('SPY', min_days=0, max_days=30)

    if nearest_exp:
        print(f"[OK] Nearest expiration: {nearest_exp}")

        # Calculate days to expiry
        exp_date = datetime.strptime(nearest_exp, '%Y-%m-%d')
        days_to_exp = (exp_date - datetime.now()).days
        print(f"     Days to expiration: {days_to_exp}")
        print()
    else:
        print("[WARNING] No expiration found in next 30 days")
        print("Trying to fetch all expirations...")
        nearest_exp = None

except Exception as e:
    print(f"[WARNING] Could not find expiration: {e}")
    print("Will try to fetch all options...")
    nearest_exp = None
    print()

# Step 5: Fetch SPY options
print("Step 5: Fetching SPY options data...")
print("(This may take 10-60 seconds depending on number of contracts...)")
print()

try:
    options = client.get_options_snapshot('SPY', expiration=nearest_exp)

    print(f"[OK] Retrieved {len(options)} SPY options")
    print()

    if len(options) == 0:
        print("[WARNING] No options data returned!")
        print()
        print("Possible reasons:")
        print("  - Options data not available with your subscription")
        print("  - Market is closed")
        print("  - Need options data entitlement")
        print()
        print("Check your Alpaca account at: https://app.alpaca.markets/")
        sys.exit(1)

except Exception as e:
    print(f"[ERROR] Failed to fetch options: {e}")
    print()
    print("Full error details:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Display sample options
print("Step 6: Sample options data (first 5 calls and puts):")
print("-" * 70)

# Separate calls and puts
calls = [opt for opt in options if opt['type'] == 'call']
puts = [opt for opt in options if opt['type'] == 'put']

print(f"\nTotal Calls: {len(calls)}")
print(f"Total Puts:  {len(puts)}")
print()

# Show first 5 calls
if calls:
    print("Sample CALL Options:")
    print(f"{'Strike':>8} {'Gamma':>10} {'Delta':>8} {'OI':>8} {'Volume':>8}")
    print("-" * 50)
    for opt in sorted(calls, key=lambda x: x['strike'])[:5]:
        print(f"${opt['strike']:>7.0f} {opt['gamma']:>10.6f} {opt['delta']:>8.2f} "
              f"{opt['open_interest']:>8} {opt['volume']:>8}")
    print()

# Show first 5 puts
if puts:
    print("Sample PUT Options:")
    print(f"{'Strike':>8} {'Gamma':>10} {'Delta':>8} {'OI':>8} {'Volume':>8}")
    print("-" * 50)
    for opt in sorted(puts, key=lambda x: x['strike'])[:5]:
        print(f"${opt['strike']:>7.0f} {opt['gamma']:>10.6f} {opt['delta']:>8.2f} "
              f"{opt['open_interest']:>8} {opt['volume']:>8}")
    print()

# Step 7: Calculate GEX for these options
print("Step 7: Calculating GEX...")
try:
    from src.gex_calculator import analyze_symbol_gex

    result = analyze_symbol_gex(
        symbol='SPY',
        options=options,
        underlying_price=spy_price
    )

    print(f"[OK] GEX Analysis Complete!")
    print()
    print("=" * 70)
    print("SPY GAMMA EXPOSURE RESULTS")
    print("=" * 70)
    print(f"Underlying Price:   ${result.underlying_price:.2f}")
    print(f"Total Call GEX:     ${result.total_call_gex:,.0f}")
    print(f"Total Put GEX:      ${result.total_put_gex:,.0f}")
    print(f"Net GEX:            ${result.net_gex:,.0f}")
    print(f"Gamma Flip Point:   ${result.gamma_flip_point:.2f}" if result.gamma_flip_point else "Gamma Flip Point:   N/A")
    print(f"Total Call OI:      {result.total_call_oi:,}")
    print(f"Total Put OI:       {result.total_put_oi:,}")
    print(f"Strikes with Data:  {len(result.per_strike)}")
    print()

    # Interpretation
    if result.net_gex > 0:
        print("Interpretation: POSITIVE NET GEX")
        print("  -> Market makers are LONG GAMMA")
        print("  -> Expect STABILIZING price action (dealers sell rallies, buy dips)")
        print("  -> LOWER volatility expected")
    elif result.net_gex < 0:
        print("Interpretation: NEGATIVE NET GEX")
        print("  -> Market makers are SHORT GAMMA")
        print("  -> Expect DESTABILIZING price action (dealers buy rallies, sell dips)")
        print("  -> HIGHER volatility expected")
    else:
        print("Interpretation: NEUTRAL GEX")
        print("  -> Balanced gamma exposure")

    print()
    print("=" * 70)
    print("SUCCESS! Your Alpaca API is working correctly!")
    print("=" * 70)
    print()
    print("This data can now be stored in the database and displayed in the dashboard.")
    print()

    # Save to database
    save = input("Save this data to database? (y/n): ").strip().lower()
    if save == 'y':
        from src.models import DatabaseManager
        db = DatabaseManager()
        db.save_gex_snapshot(result)
        print("[OK] Data saved to database!")
        print()
        print("Now refresh your dashboard to see this data!")

except Exception as e:
    print(f"[ERROR] GEX calculation failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("Test complete!")
