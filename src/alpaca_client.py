"""
Alpaca API client for fetching options data, Greeks, and underlying prices.
Handles authentication, rate limiting, pagination, and error handling.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter, Retry


logger = logging.getLogger('GammaScope.AlpacaClient')


class AlpacaClient:
    """
    Client for interacting with Alpaca Options API.

    Handles authentication, request retry logic, and data normalization.
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str):
        """
        Initialize Alpaca API client.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            base_url: Base URL for Alpaca API (paper or production)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')

        # Data API uses different URL
        self.data_url = "https://data.alpaca.markets"

        # Set up session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set authentication headers
        self.session.headers.update({
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Accept': 'application/json'
        })

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests to avoid rate limits

    def _rate_limit(self):
        """Implement rate limiting to avoid hitting API limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a rate-limited request to the Alpaca API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Requesting: {url} with params: {params}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            logger.error(f"Response content: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def get_underlying_price(self, symbol: str) -> float:
        """
        Get the current price of the underlying asset.

        Args:
            symbol: Ticker symbol (e.g., 'SPY', 'QQQ')

        Returns:
            Current price of the underlying asset

        Raises:
            ValueError: If price data is unavailable
            requests.exceptions.RequestException: If API request fails
        """
        # Use data API endpoint instead of trading API
        self._rate_limit()
        url = f"{self.data_url}/v2/stocks/{symbol}/snapshot"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Extract latest trade price
            if 'latestTrade' in data and 'p' in data['latestTrade']:
                price = float(data['latestTrade']['p'])
                logger.info(f"Got underlying price for {symbol}: ${price:.2f}")
                return price
            elif 'prevDailyBar' in data and 'c' in data['prevDailyBar']:
                # Fallback to previous close if no latest trade
                price = float(data['prevDailyBar']['c'])
                logger.warning(f"Using previous close for {symbol}: ${price:.2f}")
                return price
            else:
                raise ValueError(f"No price data available for {symbol}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get underlying price for {symbol}: {e}")
            raise

    def get_option_chain(self, symbol: str, expiration_date: Optional[str] = None) -> List[str]:
        """
        Get available option contracts for a symbol.

        Args:
            symbol: Underlying ticker symbol
            expiration_date: Optional specific expiration date (YYYY-MM-DD)

        Returns:
            List of option contract symbols

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        endpoint = "/v2/options/contracts"
        params = {
            'underlying_symbols': symbol,
            'status': 'active',
            'limit': 10000  # Maximum allowed
        }

        if expiration_date:
            params['expiration_date'] = expiration_date

        try:
            data = self._make_request(endpoint, params)
            contracts = data.get('option_contracts', [])
            contract_symbols = [c['symbol'] for c in contracts]
            logger.info(f"Found {len(contract_symbols)} option contracts for {symbol}")
            return contract_symbols

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get option chain for {symbol}: {e}")
            raise

    def get_options_snapshot(self, symbol: str, expiration: Optional[str] = None) -> List[Dict]:
        """
        Fetch options data with Greeks and open interest for a symbol.

        This is the main method for retrieving option data needed for GEX calculation.

        Args:
            symbol: Underlying ticker symbol (e.g., 'SPY')
            expiration: Optional expiration date filter (YYYY-MM-DD)

        Returns:
            List of dictionaries, each containing:
                - symbol: Option contract symbol
                - underlying_symbol: Underlying ticker
                - strike: Strike price
                - expiration: Expiration date
                - type: 'call' or 'put'
                - gamma: Gamma Greek
                - delta: Delta Greek
                - vega: Vega Greek (optional)
                - theta: Theta Greek (optional)
                - implied_volatility: IV
                - open_interest: Open interest
                - volume: Trading volume
                - bid: Bid price
                - ask: Ask price
                - last_price: Last trade price

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        # First, get the option chain
        contract_symbols = self.get_option_chain(symbol, expiration)

        if not contract_symbols:
            logger.warning(f"No option contracts found for {symbol}")
            return []

        # Fetch snapshots in batches (Alpaca allows multiple symbols in one request)
        batch_size = 100  # Adjust based on API limits
        all_options = []

        for i in range(0, len(contract_symbols), batch_size):
            batch = contract_symbols[i:i + batch_size]
            symbols_param = ','.join(batch)

            endpoint = "/v2/options/snapshots"
            params = {'symbols': symbols_param}

            try:
                data = self._make_request(endpoint, params)
                snapshots = data.get('snapshots', {})

                for contract_symbol, snapshot_data in snapshots.items():
                    option_data = self._normalize_option_data(contract_symbol, snapshot_data)
                    if option_data:
                        all_options.append(option_data)

                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} contracts")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch snapshot batch: {e}")
                continue

        logger.info(f"Retrieved {len(all_options)} options with data for {symbol}")
        return all_options

    def _normalize_option_data(self, contract_symbol: str, snapshot: Dict) -> Optional[Dict]:
        """
        Normalize option snapshot data into a standardized format.

        Args:
            contract_symbol: Option contract symbol
            snapshot: Raw snapshot data from Alpaca API

        Returns:
            Normalized option data dictionary, or None if essential data is missing
        """
        try:
            # Parse contract symbol to extract metadata
            # Alpaca format: underlying + expiry (YYMMDD) + C/P + strike
            # Example: SPY230120C00400000 = SPY call expiring 2023-01-20 at strike 400

            # Extract Greeks (may be in 'greeks' or at root level)
            greeks = snapshot.get('greeks', {})

            # Check for required fields
            if not greeks.get('gamma'):
                logger.debug(f"Skipping {contract_symbol}: missing gamma")
                return None

            # Get latest quote and trade data
            latest_quote = snapshot.get('latestQuote', {})
            latest_trade = snapshot.get('latestTrade', {})

            option_data = {
                'symbol': contract_symbol,
                'underlying_symbol': snapshot.get('underlying_symbol', ''),
                'strike': float(snapshot.get('strike_price', 0)),
                'expiration': snapshot.get('expiration_date', ''),
                'type': snapshot.get('type', '').lower(),  # 'call' or 'put'
                'gamma': float(greeks.get('gamma', 0)),
                'delta': float(greeks.get('delta', 0)),
                'vega': float(greeks.get('vega', 0)),
                'theta': float(greeks.get('theta', 0)),
                'implied_volatility': float(snapshot.get('implied_volatility', 0)),
                'open_interest': int(snapshot.get('open_interest', 0)),
                'volume': int(snapshot.get('volume', 0)),
                'bid': float(latest_quote.get('bp', 0)),
                'ask': float(latest_quote.get('ap', 0)),
                'last_price': float(latest_trade.get('p', 0)),
            }

            return option_data

        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Error normalizing option data for {contract_symbol}: {e}")
            return None

    def get_nearest_expiration(self, symbol: str, min_days: int = 0, max_days: int = 60) -> Optional[str]:
        """
        Find the nearest expiration date within a date range.

        Args:
            symbol: Underlying ticker symbol
            min_days: Minimum days to expiration
            max_days: Maximum days to expiration

        Returns:
            Expiration date string (YYYY-MM-DD) or None if not found
        """
        today = datetime.now().date()
        min_date = today + timedelta(days=min_days)
        max_date = today + timedelta(days=max_days)

        endpoint = "/v2/options/contracts"
        params = {
            'underlying_symbols': symbol,
            'status': 'active',
            'limit': 1000
        }

        try:
            data = self._make_request(endpoint, params)
            contracts = data.get('option_contracts', [])

            # Extract unique expiration dates
            expirations = set()
            for contract in contracts:
                exp_str = contract.get('expiration_date', '')
                if exp_str:
                    exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
                    if min_date <= exp_date <= max_date:
                        expirations.add(exp_str)

            if expirations:
                # Return the nearest expiration
                nearest = min(expirations)
                logger.info(f"Nearest expiration for {symbol}: {nearest}")
                return nearest

            logger.warning(f"No expirations found for {symbol} in range {min_days}-{max_days} days")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to find nearest expiration for {symbol}: {e}")
            return None


# Example usage and testing
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    # Load environment
    load_dotenv()

    # Initialize client
    client = AlpacaClient(
        api_key=os.getenv('ALPACA_API_KEY'),
        secret_key=os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL')
    )

    # Test underlying price
    try:
        spy_price = client.get_underlying_price('SPY')
        print(f"SPY Price: ${spy_price:.2f}")
    except Exception as e:
        print(f"Error getting SPY price: {e}")

    # Test option chain
    try:
        nearest_exp = client.get_nearest_expiration('SPY', max_days=30)
        if nearest_exp:
            options = client.get_options_snapshot('SPY', expiration=nearest_exp)
            print(f"Found {len(options)} options for SPY expiring {nearest_exp}")

            if options:
                print("\nSample option:")
                print(options[0])
    except Exception as e:
        print(f"Error getting options: {e}")
