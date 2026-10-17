"""
Polygon.io API client for fetching options data with Greeks.

Provides access to options chains, Greeks (gamma, delta, etc.),
open interest, and underlying prices via Polygon.io REST API.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter, Retry


logger = logging.getLogger('GammaScope.PolygonClient')


class PolygonClient:
    """
    Client for interacting with Polygon.io Options API.

    Handles authentication, rate limiting, and data normalization.
    """

    def __init__(self, api_key: str, min_request_interval: float = 12.0):
        """
        Initialize Polygon.io API client.

        Args:
            api_key: Polygon.io API key
            min_request_interval: Seconds between requests (12 = free tier, 5/min;
                paid tiers can go much lower)
        """
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"

        # Set up session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = min_request_interval

        logger.info("Polygon.io client initialized")

    def _rate_limit(self):
        """Implement rate limiting (5 calls/minute for free tier)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a rate-limited request to Polygon.io API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        self._rate_limit()

        if params is None:
            params = {}

        # Add API key to params
        params['apiKey'] = self.api_key

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Requesting: {url}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check for error in response
            if data.get('status') == 'ERROR':
                error_msg = data.get('error', 'Unknown error')
                logger.error(f"Polygon API error: {error_msg}")
                raise ValueError(f"Polygon API error: {error_msg}")

            return data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            if e.response is not None:
                logger.error(f"Response: {e.response.text}")
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
        endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"

        try:
            data = self._make_request(endpoint)

            ticker_data = data.get('ticker', {})

            # Try to get last trade price
            if 'lastTrade' in ticker_data:
                price = float(ticker_data['lastTrade'].get('p', 0))
                if price > 0:
                    logger.info(f"Got underlying price for {symbol}: ${price:.2f}")
                    return price

            # Plans without trade data (e.g. Starter) omit lastTrade from the
            # snapshot but still return the current session's bars: the latest
            # minute bar, then the day bar. Both are zero/absent before the open.
            for bar in ('min', 'day'):
                price = float((ticker_data.get(bar) or {}).get('c', 0) or 0)
                if price > 0:
                    logger.info(f"Got underlying price for {symbol} from {bar} bar: ${price:.2f}")
                    return price

            # Last resort: previous close (stale by up to a session)
            if 'prevDay' in ticker_data:
                price = float(ticker_data['prevDay'].get('c', 0))
                if price > 0:
                    logger.warning(f"Using previous close for {symbol}: ${price:.2f}")
                    return price

            raise ValueError(f"No price data available for {symbol}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get underlying price for {symbol}: {e}")
            raise

    def get_options_snapshot(
        self,
        symbol: str,
        expiration: Optional[str] = None,
        expiration_min: Optional[str] = None,
        expiration_max: Optional[str] = None,
        max_options: int = 5000,
    ) -> List[Dict]:
        """
        Fetch options data with Greeks and open interest for a symbol.

        This is the main method for retrieving option data needed for GEX calculation.

        Args:
            symbol: Underlying ticker symbol (e.g., 'SPY')
            expiration: Optional single expiration date filter (YYYY-MM-DD)
            expiration_min: Optional earliest expiration (inclusive) for a multi-expiry book
            expiration_max: Optional latest expiration (inclusive) for a multi-expiry book
            max_options: Safety cap on contracts fetched across all pages

        Returns:
            List of dictionaries, each containing:
                - symbol: Option contract symbol
                - underlying_symbol: Underlying ticker
                - strike: Strike price
                - expiration: Expiration date
                - type: 'call' or 'put'
                - gamma: Gamma Greek
                - delta: Delta Greek
                - vega: Vega Greek
                - theta: Theta Greek
                - implied_volatility: IV
                - open_interest: Open interest
                - volume: Trading volume
                - bid: Bid price
                - ask: Ask price
                - last_price: Last trade price

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        endpoint = f"/v3/snapshot/options/{symbol}"

        params = {
            'limit': 250  # Max allowed per request
        }

        if expiration:
            params['expiration_date'] = expiration
        if expiration_min:
            params['expiration_date.gte'] = expiration_min
        if expiration_max:
            params['expiration_date.lte'] = expiration_max

        all_options = []

        try:
            # Fetch options snapshot
            data = self._make_request(endpoint, params)

            results = data.get('results', [])

            if not results:
                logger.warning(f"No options data returned for {symbol}")
                return []

            # Process each option
            for option_data in results:
                normalized = self._normalize_option_data(option_data, symbol)
                if normalized:
                    all_options.append(normalized)

            logger.info(f"Retrieved {len(all_options)} options for {symbol}")

            # Handle pagination if needed
            next_url = data.get('next_url')
            while next_url and len(all_options) < max_options:  # Safety limit
                logger.info(f"Fetching next page of options...")
                self._rate_limit()

                try:
                    response = self.session.get(next_url, params={'apiKey': self.api_key}, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    results = data.get('results', [])
                    for option_data in results:
                        normalized = self._normalize_option_data(option_data, symbol)
                        if normalized:
                            all_options.append(normalized)

                    next_url = data.get('next_url')

                except Exception as e:
                    logger.warning(f"Error fetching next page: {e}")
                    break

            return all_options

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch options for {symbol}: {e}")
            raise

    def _normalize_option_data(self, option_data: Dict, underlying_symbol: str) -> Optional[Dict]:
        """
        Normalize Polygon.io option data into standard format.

        Args:
            option_data: Raw option data from Polygon.io
            underlying_symbol: Underlying ticker symbol

        Returns:
            Normalized option data dictionary, or None if essential data missing
        """
        try:
            details = option_data.get('details', {})
            greeks = option_data.get('greeks', {})

            # Check for gamma (required for GEX)
            if not greeks.get('gamma'):
                logger.debug(f"Skipping option: missing gamma")
                return None

            # Get quote data
            last_quote = option_data.get('last_quote', {})
            last_trade = option_data.get('last_trade', {})

            # Determine option type
            contract_type = details.get('contract_type', '').lower()
            if contract_type not in ['call', 'put']:
                logger.debug(f"Skipping option: invalid type {contract_type}")
                return None

            normalized = {
                'symbol': details.get('ticker', ''),
                'underlying_symbol': underlying_symbol,
                'strike': float(details.get('strike_price', 0)),
                'expiration': details.get('expiration_date', ''),
                'type': contract_type,
                'gamma': float(greeks.get('gamma', 0)),
                'delta': float(greeks.get('delta', 0)),
                'vega': float(greeks.get('vega', 0)),
                'theta': float(greeks.get('theta', 0)),
                'implied_volatility': float(option_data.get('implied_volatility', 0)),
                'open_interest': int(option_data.get('open_interest', 0)),
                'volume': int(option_data.get('day', {}).get('volume', 0)),
                'bid': float(last_quote.get('bid', 0)),
                'ask': float(last_quote.get('ask', 0)),
                'last_price': float(last_trade.get('price', 0)),
            }

            return normalized

        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Error normalizing option data: {e}")
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
        endpoint = f"/v3/reference/options/contracts"

        today = datetime.now().date()
        min_date = today + timedelta(days=min_days)
        max_date = today + timedelta(days=max_days)

        params = {
            'underlying_ticker': symbol,
            'expired': 'false',
            'limit': 250
        }

        try:
            data = self._make_request(endpoint, params)
            results = data.get('results', [])

            if not results:
                logger.warning(f"No option contracts found for {symbol}")
                return None

            # Extract unique expiration dates in range
            expirations = set()
            for contract in results:
                exp_str = contract.get('expiration_date', '')
                if exp_str:
                    try:
                        exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
                        if min_date <= exp_date <= max_date:
                            expirations.add(exp_str)
                    except ValueError:
                        continue

            if expirations:
                nearest = min(expirations)
                logger.info(f"Nearest expiration for {symbol}: {nearest}")
                return nearest

            logger.warning(f"No expirations found for {symbol} in range {min_days}-{max_days} days")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to find expiration for {symbol}: {e}")
            return None


# Example usage
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('POLYGON_API_KEY')

    if not api_key:
        print("Error: POLYGON_API_KEY not found in .env")
        print("Get your free API key at: https://polygon.io/")
        exit(1)

    # Initialize client
    client = PolygonClient(api_key)

    # Test underlying price
    try:
        spy_price = client.get_underlying_price('SPY')
        print(f"SPY Price: ${spy_price:.2f}")
    except Exception as e:
        print(f"Error getting SPY price: {e}")

    # Test nearest expiration
    try:
        nearest_exp = client.get_nearest_expiration('SPY', max_days=30)
        print(f"Nearest SPY expiration: {nearest_exp}")
    except Exception as e:
        print(f"Error getting expiration: {e}")

    # Test options snapshot
    try:
        print("\nFetching SPY options (this may take a minute due to rate limits)...")
        options = client.get_options_snapshot('SPY', expiration=nearest_exp)
        print(f"Found {len(options)} options")

        if options:
            print("\nSample option:")
            print(options[0])
    except Exception as e:
        print(f"Error getting options: {e}")
