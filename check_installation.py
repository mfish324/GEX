"""
GammaScope Installation Checker

Run this script to verify all dependencies are properly installed.
"""
import sys

print("=" * 60)
print("GammaScope Installation Checker")
print("=" * 60)
print()

# Check Python version
print(f"Python Version: {sys.version}")
print(f"Python Path: {sys.executable}")
print()

# Required packages
required_packages = [
    'dotenv',
    'requests',
    'pandas',
    'numpy',
    'alpaca',
    'sqlalchemy',
    'apscheduler',
    'plotly',
    'matplotlib',
    'streamlit',
    'pytest',
]

print("Checking required packages...")
print("-" * 60)

missing_packages = []
installed_packages = []

for package in required_packages:
    try:
        if package == 'dotenv':
            import dotenv
            version = getattr(dotenv, '__version__', 'installed')
            package_name = 'python-dotenv'
        elif package == 'alpaca':
            import alpaca
            version = getattr(alpaca, '__version__', 'installed')
            package_name = 'alpaca-py'
        else:
            module = __import__(package)
            version = getattr(module, '__version__', 'installed')
            package_name = package

        print(f"[OK] {package_name:20s} {version}")
        installed_packages.append(package_name)
    except (ImportError, AttributeError) as e:
        print(f"[MISSING] {package:20s} NOT FOUND")
        missing_packages.append(package)

print("-" * 60)
print()

# Summary
if missing_packages:
    print(f"[ERROR] {len(missing_packages)} package(s) missing:")
    for pkg in missing_packages:
        print(f"   - {pkg}")
    print()
    print("To install missing packages:")
    print("   pip install -r requirements.txt")
    print()
    sys.exit(1)
else:
    print(f"[SUCCESS] All {len(installed_packages)} required packages are installed!")
    print()

# Check if .env exists
import os
if os.path.exists('.env'):
    print("[OK] .env file exists")
else:
    print("[WARNING] .env file not found (required for live data)")
    print("          Copy .env.example to .env and add your Alpaca credentials")

# Check if config.json exists
if os.path.exists('config.json'):
    print("[OK] config.json exists")

    # Check sample mode
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)

    if config.get('sample_mode', False):
        print("     Running in SAMPLE MODE (demo data)")
    else:
        print("     Running in LIVE MODE (requires Alpaca credentials)")
else:
    print("[ERROR] config.json not found")

# Check if data directory exists
if os.path.exists('data'):
    print("[OK] data directory exists")
else:
    print("[INFO] data directory not found (will be created automatically)")

print()
print("=" * 60)
print("Installation Status: OK")
print("=" * 60)
print()
print("You can now run GammaScope:")
print("   python main.py              # Full system")
print("   python main.py --webapp     # UI only")
print("   python main.py --debug      # Debug mode")
print()
print("Or use the helper scripts:")
print("   run_demo.bat               # Demo mode (Windows)")
print("   run.bat                    # Live mode (Windows)")
print()
