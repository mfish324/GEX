"""
Utility functions for configuration, environment loading, and common helpers.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv


# Configure logging
def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Configure application logging.

    Args:
        debug: If True, set log level to DEBUG, otherwise INFO

    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('GammaScope')


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path object pointing to project root
    """
    return Path(__file__).parent.parent


def load_env_config() -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Returns:
        Dictionary containing environment configuration

    Raises:
        ValueError: If required environment variables are missing
    """
    root = get_project_root()
    env_path = root / '.env'

    # Load .env file if it exists
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logging.warning(f".env file not found at {env_path}. Using environment variables.")

    # Determine data provider
    provider = os.getenv('DATA_PROVIDER', 'polygon').lower()
    config = {'DATA_PROVIDER': provider}

    # Load provider-specific credentials
    if provider == 'alpaca':
        required_vars = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'ALPACA_BASE_URL']
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                raise ValueError(f"Required environment variable {var} is not set for Alpaca. "
                               f"Please create a .env file based on .env.example")
            config[var] = value
    elif provider == 'polygon':
        polygon_key = os.getenv('POLYGON_API_KEY')
        if not polygon_key:
            raise ValueError("POLYGON_API_KEY is not set. "
                           "Get your free API key from https://polygon.io/ "
                           "and add it to your .env file")
        config['POLYGON_API_KEY'] = polygon_key
    else:
        raise ValueError(f"Unknown DATA_PROVIDER: {provider}. Must be 'alpaca' or 'polygon'")

    # Optional variables
    config['DEBUG'] = os.getenv('DEBUG', 'false').lower() == 'true'

    return config


def load_json_config() -> Dict[str, Any]:
    """
    Load application configuration from config.json.

    Returns:
        Dictionary containing application configuration

    Raises:
        FileNotFoundError: If config.json is not found
        json.JSONDecodeError: If config.json is invalid
    """
    root = get_project_root()
    config_path = root / 'config.json'

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Validate required fields
    required_fields = ['symbols', 'refresh_interval_minutes']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required configuration field '{field}' missing in config.json")

    # Set defaults for optional fields
    if 'contract_multipliers' not in config:
        config['contract_multipliers'] = {symbol: 100 for symbol in config['symbols']}

    if 'sample_mode' not in config:
        config['sample_mode'] = False

    if 'data_retention_days' not in config:
        config['data_retention_days'] = 7

    return config


def save_json_config(config: Dict[str, Any]) -> None:
    """
    Save application configuration to config.json.

    Args:
        config: Configuration dictionary to save
    """
    root = get_project_root()
    config_path = root / 'config.json'

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def get_contract_multiplier(symbol: str, config: Dict[str, Any]) -> int:
    """
    Get the contract multiplier for a given symbol.

    Args:
        symbol: Ticker symbol (e.g., 'SPY', 'SPX')
        config: Application configuration dictionary

    Returns:
        Contract multiplier (typically 100 for standard equity options)
    """
    return config.get('contract_multipliers', {}).get(symbol, 100)


def format_large_number(num: float) -> str:
    """
    Format large numbers with appropriate suffixes (K, M, B, T).

    Args:
        num: Number to format

    Returns:
        Formatted string (e.g., "1.23M", "-456.78K")
    """
    abs_num = abs(num)
    sign = '-' if num < 0 else ''

    if abs_num >= 1e12:
        return f"{sign}{abs_num/1e12:.2f}T"
    elif abs_num >= 1e9:
        return f"{sign}{abs_num/1e9:.2f}B"
    elif abs_num >= 1e6:
        return f"{sign}{abs_num/1e6:.2f}M"
    elif abs_num >= 1e3:
        return f"{sign}{abs_num/1e3:.2f}K"
    else:
        return f"{sign}{abs_num:.2f}"


def validate_symbols(symbols: List[str]) -> List[str]:
    """
    Validate and sanitize ticker symbols.

    Args:
        symbols: List of ticker symbols

    Returns:
        List of validated, uppercase symbols
    """
    validated = []
    for symbol in symbols:
        clean_symbol = symbol.strip().upper()
        if clean_symbol and clean_symbol.isalpha():
            validated.append(clean_symbol)
        else:
            logging.warning(f"Invalid symbol '{symbol}' skipped")

    return validated


class Config:
    """
    Singleton configuration class that combines environment and JSON config.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize configuration from environment and JSON files."""
        self.env = load_env_config()
        self.app = load_json_config()
        self.logger = setup_logging(self.env['DEBUG'])

    def reload(self):
        """Reload configuration from files."""
        self._initialize()

    @property
    def symbols(self) -> List[str]:
        """Get list of tracked symbols."""
        return self.app['symbols']

    @property
    def refresh_interval_minutes(self) -> int:
        """Get refresh interval in minutes."""
        return self.app['refresh_interval_minutes']

    @property
    def sample_mode(self) -> bool:
        """Check if running in sample mode (offline demo)."""
        return self.app.get('sample_mode', False)

    def get_multiplier(self, symbol: str) -> int:
        """Get contract multiplier for symbol."""
        return get_contract_multiplier(symbol, self.app)
