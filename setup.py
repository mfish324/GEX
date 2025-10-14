"""
Setup script for GammaScope

Quick setup helper that checks requirements and guides the user through configuration.
"""
import os
import sys
from pathlib import Path
import subprocess


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(step_num, text):
    """Print a numbered step."""
    print(f"\n[Step {step_num}] {text}")


def check_python_version():
    """Check if Python version is adequate."""
    print_step(1, "Checking Python version...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required. You have Python {version.major}.{version.minor}.{version.micro}")
        return False

    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_venv():
    """Check if running in a virtual environment."""
    print_step(2, "Checking virtual environment...")

    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("⚠️  Not running in a virtual environment")
        print("   Recommended: create a venv first")
        print("   python -m venv venv")
        print("   Then activate it:")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        return False

    print("✓ Running in virtual environment")
    return True


def install_dependencies():
    """Install required dependencies."""
    print_step(3, "Installing dependencies...")

    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    try:
        print("Installing packages from requirements.txt...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_env_file():
    """Guide user through .env setup."""
    print_step(4, "Setting up environment variables...")

    env_path = Path(__file__).parent / ".env"
    env_example_path = Path(__file__).parent / ".env.example"

    if env_path.exists():
        print("⚠️  .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping .env setup")
            return True

    # Copy example
    if env_example_path.exists():
        with open(env_example_path, 'r') as f:
            content = f.read()

        print("\nPlease provide your Alpaca API credentials:")
        print("(You can get these from: https://app.alpaca.markets/paper/dashboard/overview)")

        api_key = input("\nAlpaca API Key: ").strip()
        secret_key = input("Alpaca Secret Key: ").strip()

        use_paper = input("Use paper trading? (Y/n): ").strip().lower()
        if use_paper != 'n':
            base_url = "https://paper-api.alpaca.markets"
        else:
            base_url = "https://api.alpaca.markets"

        # Replace placeholders
        content = content.replace("your_api_key_here", api_key)
        content = content.replace("your_secret_key_here", secret_key)
        content = content.replace("https://paper-api.alpaca.markets", base_url)

        with open(env_path, 'w') as f:
            f.write(content)

        print("\n✓ .env file created")
        return True
    else:
        print("❌ .env.example not found")
        return False


def verify_config():
    """Verify config.json exists."""
    print_step(5, "Verifying configuration...")

    config_path = Path(__file__).parent / "config.json"

    if not config_path.exists():
        print("❌ config.json not found")
        return False

    print("✓ config.json found")

    # Ask if user wants to modify symbols
    modify = input("\nDo you want to modify tracked symbols? (y/N): ").strip().lower()
    if modify == 'y':
        print("\nEdit config.json to change tracked symbols")
        print("Default symbols: SPY, QQQ, SPX")

    return True


def run_tests():
    """Run unit tests."""
    print_step(6, "Running tests (optional)...")

    run = input("Run unit tests? (Y/n): ").strip().lower()
    if run == 'n':
        print("Skipping tests")
        return True

    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])
        print("✓ All tests passed")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed (this may be expected)")
        return True


def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete!")

    print("Next steps:\n")
    print("1. Review your configuration:")
    print("   - Check .env for API credentials")
    print("   - Edit config.json to customize symbols\n")

    print("2. Run GammaScope:")
    print("   python main.py\n")

    print("3. Access the dashboard:")
    print("   Open http://localhost:8501 in your browser\n")

    print("4. For demo mode (no API required):")
    print("   - Set 'sample_mode': true in config.json")
    print("   - Run: python main.py\n")

    print("Additional commands:")
    print("  python main.py --help         Show all options")
    print("  python main.py --once         Fetch data once")
    print("  python main.py --scheduler    Run scheduler only")
    print("  python main.py --webapp       Run webapp only\n")

    print("For help and documentation, see README.md")
    print("\nHappy trading! 📊")


def main():
    """Main setup routine."""
    print_header("GammaScope Setup Wizard")

    print("This wizard will help you set up GammaScope.\n")

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check virtual environment
    venv_ok = check_venv()
    if not venv_ok:
        proceed = input("\nProceed anyway? (y/N): ").strip().lower()
        if proceed != 'y':
            print("\nPlease create and activate a virtual environment first.")
            sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        sys.exit(1)

    # Setup .env
    if not setup_env_file():
        print("\n❌ Setup failed: Could not create .env file")
        print("You can manually create it based on .env.example")

    # Verify config
    if not verify_config():
        print("\n❌ Setup failed: config.json missing")
        sys.exit(1)

    # Run tests (optional)
    run_tests()

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)
