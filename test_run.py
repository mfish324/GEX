"""
Quick test script to verify GammaScope components work.
Run this to test without starting the full application.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("GammaScope Component Test")
print("=" * 60)
print()

# Test 1: Config loading
print("1. Testing configuration loading...")
try:
    from src.utils import Config
    config = Config()
    print(f"   [OK] Config loaded")
    print(f"   - Symbols: {', '.join(config.symbols)}")
    print(f"   - Sample mode: {config.sample_mode}")
    print(f"   - Refresh interval: {config.refresh_interval_minutes} min")
except Exception as e:
    print(f"   [ERROR] Config failed: {e}")
    sys.exit(1)

print()

# Test 2: Database
print("2. Testing database connection...")
try:
    from src.models import DatabaseManager
    db = DatabaseManager()
    print(f"   [OK] Database initialized at: {db.db_path}")
except Exception as e:
    print(f"   [ERROR] Database failed: {e}")
    sys.exit(1)

print()

# Test 3: GEX Calculator
print("3. Testing GEX calculator...")
try:
    from src.gex_calculator import compute_option_gex, aggregate_gex

    # Test single option
    test_option = {
        'type': 'call',
        'gamma': 0.005,
        'delta': 0.5,
        'open_interest': 10000,
        'strike': 450
    }
    gex = compute_option_gex(test_option, 450.0)
    print(f"   [OK] GEX calculator working")
    print(f"   - Test option GEX: ${gex:,.0f}")
except Exception as e:
    print(f"   [ERROR] GEX calculator failed: {e}")
    sys.exit(1)

print()

# Test 4: Visualization
print("4. Testing visualization module...")
try:
    from src.visualization import plot_gex_vs_strike
    print(f"   [OK] Visualization module loaded")
except Exception as e:
    print(f"   [ERROR] Visualization failed: {e}")
    sys.exit(1)

print()

# Test 5: Sample mode data
if config.sample_mode:
    print("5. Testing sample mode...")
    try:
        from src.webapp import load_sample_data
        sample_data = load_sample_data()
        print(f"   [OK] Sample data loaded")
        print(f"   - Available symbols: {', '.join(sample_data.keys())}")

        # Show SPY data
        if 'SPY' in sample_data:
            spy = sample_data['SPY']
            print(f"   - SPY price: ${spy['underlying_price']:.2f}")
            print(f"   - SPY net GEX: ${spy['net_gex']:,.0f}")
    except Exception as e:
        print(f"   [ERROR] Sample data failed: {e}")

print()
print("=" * 60)
print("All Components Working!")
print("=" * 60)
print()
print("Ready to run GammaScope:")
print("  python main.py")
print()
print("Or for webapp only:")
print("  python main.py --webapp")
print()
