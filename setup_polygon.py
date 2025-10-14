"""
Interactive setup script for Polygon.io integration with GammaScope
"""
import os
import sys
from pathlib import Path

print("=" * 70)
print("GammaScope - Polygon.io Setup Wizard")
print("=" * 70)
print()
print("This wizard will help you set up Polygon.io as your data provider.")
print()

# Step 1: Check if .env exists
env_path = Path('.env')
if not env_path.exists():
    print("[Step 1] Creating .env file...")
    # Copy from example
    example_path = Path('.env.example')
    if example_path.exists():
        import shutil
        shutil.copy(example_path, env_path)
        print("✓ .env file created from .env.example")
    else:
        print("✗ .env.example not found!")
        sys.exit(1)
else:
    print("[Step 1] .env file already exists")

print()

# Step 2: Get API key
print("[Step 2] Polygon.io API Key")
print()
print("You need a free API key from Polygon.io:")
print("1. Go to: https://polygon.io/")
print("2. Click 'Sign Up Free'")
print("3. After signing up, go to Dashboard → API Keys")
print("4. Copy your API key")
print()

api_key = input("Paste your Polygon.io API key here (or press Enter to skip): ").strip()

if api_key:
    # Update .env file
    print("\nUpdating .env file...")

    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update or add POLYGON_API_KEY and DATA_PROVIDER
    updated = False
    provider_set = False

    for i, line in enumerate(lines):
        if line.startswith('POLYGON_API_KEY='):
            lines[i] = f'POLYGON_API_KEY={api_key}\n'
            updated = True
        elif line.startswith('DATA_PROVIDER='):
            lines[i] = 'DATA_PROVIDER=polygon\n'
            provider_set = True

    if not updated:
        lines.append(f'\nPOLYGON_API_KEY={api_key}\n')
    if not provider_set:
        lines.insert(0, 'DATA_PROVIDER=polygon\n')

    with open(env_path, 'w') as f:
        f.writelines(lines)

    print("✓ .env file updated with your API key")
else:
    print("\nSkipped. You can add your API key to .env manually later.")
    print("Just add this line to .env:")
    print("  POLYGON_API_KEY=your_key_here")

print()

# Step 3: Update config.json
print("[Step 3] Updating config.json for optimal settings...")

import json

config_path = Path('config.json')
if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Update settings for free tier
    config['sample_mode'] = False
    config['symbols'] = ['SPY']  # Start with one symbol
    config['refresh_interval_minutes'] = 15  # Safe for free tier

    # Set expiration filter
    if 'expiration_filter' not in config:
        config['expiration_filter'] = {}

    config['expiration_filter']['use_nearest_expiry'] = True
    config['expiration_filter']['days_to_expiry_max'] = 30

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print("✓ config.json updated:")
    print("  - sample_mode: false")
    print("  - symbols: [SPY]")
    print("  - refresh_interval: 15 minutes")
    print("  - use_nearest_expiry: true")
else:
    print("✗ config.json not found!")

print()

# Step 4: Test connection
if api_key:
    print("[Step 4] Testing Polygon.io connection...")
    print()

    test = input("Test connection now? (Y/n): ").strip().lower()

    if test != 'n':
        print("\nTesting...")

        sys.path.insert(0, str(Path('src')))

        try:
            from src.polygon_client import PolygonClient

            client = PolygonClient(api_key)

            # Test underlying price
            try:
                spy_price = client.get_underlying_price('SPY')
                print(f"✓ SPY Price: ${spy_price:.2f}")
            except Exception as e:
                print(f"✗ Failed to get SPY price: {e}")
                sys.exit(1)

            # Test nearest expiration
            try:
                nearest_exp = client.get_nearest_expiration('SPY', max_days=30)
                print(f"✓ Nearest expiration: {nearest_exp}")
            except Exception as e:
                print(f"✗ Failed to get expiration: {e}")

            print()
            print("=" * 70)
            print("SUCCESS! Polygon.io is working correctly!")
            print("=" * 70)

        except Exception as e:
            print(f"\n✗ Error: {e}")
            print("\nPlease check:")
            print("  1. Your API key is correct")
            print("  2. You have an active internet connection")
            print("  3. Polygon.io service is online: https://status.polygon.io/")
            sys.exit(1)
else:
    print("[Step 4] Skipped (no API key provided)")

print()

# Step 5: Next steps
print("=" * 70)
print("Setup Complete!")
print("=" * 70)
print()
print("Next steps:")
print()
print("1. Run GammaScope:")
print("   python main.py")
print()
print("2. Open dashboard:")
print("   http://localhost:8501")
print()
print("3. Wait for initial data load (1-2 minutes)")
print()
print("4. View live GEX data for SPY!")
print()
print("Tips:")
print("  - Free tier: 5 API calls/minute (you're configured for this)")
print("  - Initial load takes time due to rate limiting")
print("  - Monitor usage: https://polygon.io/dashboard/api-keys")
print("  - Upgrade for more symbols/faster updates: https://polygon.io/pricing")
print()
print("Documentation: See POLYGON_SETUP.md for detailed guide")
print()
