"""
Simple Alpaca API Test - Try different endpoints
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')
base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

print("=" * 70)
print("Alpaca API Endpoint Test")
print("=" * 70)
print(f"API Key: {api_key[:15]}...")
print(f"Base URL: {base_url}")
print()

headers = {
    'APCA-API-KEY-ID': api_key,
    'APCA-API-SECRET-KEY': secret_key
}

# Test 1: Account endpoint
print("Test 1: Account Info")
try:
    resp = requests.get(f"{base_url}/v2/account", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"[OK] Account Status: {data.get('status')}")
        print(f"     Trading Blocked: {data.get('trading_blocked')}")
        print(f"     Account Blocked: {data.get('account_blocked')}")
    else:
        print(f"[ERROR] {resp.text}")
except Exception as e:
    print(f"[ERROR] {e}")
print()

# Test 2: Try data API (different URL)
print("Test 2: Market Data API (data.alpaca.markets)")
data_url = "https://data.alpaca.markets"
try:
    resp = requests.get(
        f"{data_url}/v2/stocks/SPY/snapshot",
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"[OK] SPY Price: ${data.get('latestTrade', {}).get('p', 'N/A')}")
    else:
        print(f"[ERROR] {resp.text}")
except Exception as e:
    print(f"[ERROR] {e}")
print()

# Test 3: Try latest trade endpoint
print("Test 3: Latest Trade Endpoint")
try:
    resp = requests.get(
        f"{data_url}/v2/stocks/SPY/trades/latest",
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        trade = data.get('trade', {})
        print(f"[OK] SPY Latest Trade: ${trade.get('p', 'N/A')}")
    else:
        print(f"[ERROR] {resp.text}")
except Exception as e:
    print(f"[ERROR] {e}")
print()

# Test 4: Options contracts endpoint
print("Test 4: Options Contracts Endpoint")
try:
    resp = requests.get(
        f"{base_url}/v2/options/contracts",
        headers=headers,
        params={'underlying_symbols': 'SPY', 'status': 'active', 'limit': 5}
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        contracts = data.get('option_contracts', [])
        print(f"[OK] Found {len(contracts)} SPY option contracts")
        if contracts:
            print(f"     Sample: {contracts[0].get('symbol', 'N/A')}")
    else:
        print(f"[ERROR] {resp.text}")
except Exception as e:
    print(f"[ERROR] {e}")
print()

print("=" * 70)
print("Diagnosis:")
print("=" * 70)
print()
print("If all tests failed:")
print("  1. Check your API keys are correct")
print("  2. Make sure you have data subscription")
print("  3. Visit: https://app.alpaca.markets/paper/dashboard/overview")
print()
print("If only market data failed:")
print("  - You may need to enable market data feed")
print("  - Options data might require special subscription")
print()
