"""
Scheduler for periodic GEX data refresh using APScheduler.

Fetches options data, calculates GEX, and stores results in database
at configurable intervals.
"""
import inspect
import logging
import time
from datetime import date, datetime, timedelta
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .gex_calculator import analyze_symbol_gex
from .models import DatabaseManager
from .utils import Config


logger = logging.getLogger('GammaScope.Scheduler')


class GEXScheduler:
    """
    Manages periodic data refresh for GEX calculation.
    """

    def __init__(
        self,
        config: Config,
        data_client,  # Can be AlpacaClient or PolygonClient
        db_manager: DatabaseManager
    ):
        """
        Initialize GEX scheduler.

        Args:
            config: Configuration object
            data_client: Data API client (AlpacaClient or PolygonClient)
            db_manager: Database manager
        """
        self.config = config
        self.client = data_client
        self.db = db_manager

        # Create scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        self._job_id = None
        self._running = False

        logger.info("GEX Scheduler initialized")

    def start(self):
        """Start the periodic refresh job."""
        if self._job_id is not None:
            logger.warning("Scheduler already running")
            return

        interval_minutes = self.config.refresh_interval_minutes

        # Add job and store the job ID string, not the Job object
        job = self.scheduler.add_job(
            func=self.refresh_all_symbols,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='gex_refresh',
            name='GEX Data Refresh',
            replace_existing=True
        )
        self._job_id = 'gex_refresh'  # Store the job ID string

        logger.info(f"Scheduler started with {interval_minutes}-minute refresh interval")

        # Run initial refresh
        logger.info("Running initial data refresh...")
        self.refresh_all_symbols()

    def stop(self):
        """Stop the scheduler."""
        if self._job_id:
            self.scheduler.remove_job(self._job_id)
            self._job_id = None
            logger.info("Scheduler stopped")

    def shutdown(self):
        """Shutdown the scheduler completely."""
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down")

    def refresh_all_symbols(self):
        """
        Refresh GEX data for all configured symbols.

        This is the main job function that runs periodically.
        """
        if self._running:
            logger.warning("Refresh already in progress, skipping...")
            return

        self._running = True
        start_time = time.time()

        symbols = self.config.symbols
        logger.info(f"Starting refresh for symbols: {', '.join(symbols)}")

        success_count = 0
        error_count = 0
        total_records = 0
        errors = []

        for symbol in symbols:
            try:
                logger.info(f"Refreshing {symbol}...")
                result = self.refresh_symbol(symbol)

                if result:
                    success_count += 1
                    total_records += 1
                    logger.info(f"✓ {symbol} refreshed successfully")
                else:
                    error_count += 1
                    logger.warning(f"✗ {symbol} refresh returned no data")

            except Exception as e:
                error_count += 1
                error_msg = f"{symbol}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"✗ Error refreshing {symbol}: {e}", exc_info=True)

        # Calculate duration
        duration = time.time() - start_time

        # Determine status
        if error_count == 0:
            status = 'success'
        elif success_count > 0:
            status = 'partial'
        else:
            status = 'failed'

        # Log to database
        error_message = '; '.join(errors) if errors else None
        self.db.log_refresh(
            symbols=symbols,
            status=status,
            duration=duration,
            error=error_message,
            records=total_records
        )

        logger.info(f"Refresh complete: {success_count} success, {error_count} errors, "
                   f"{duration:.2f}s elapsed")

        self._running = False

    def refresh_symbol(self, symbol: str) -> bool:
        """
        Refresh GEX data for a single symbol.

        Args:
            symbol: Ticker symbol to refresh

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get underlying price
            underlying_price = self.client.get_underlying_price(symbol)
            logger.debug(f"{symbol} underlying price: ${underlying_price:.2f}")

            # Get option chain
            # For production, you might want to filter by expiration
            # For now, get all active options (may be slow for high-volume symbols)
            expiration_config = self.config.app.get('expiration_filter', {})

            book_kwargs = {}
            if expiration_config.get('full_book', False):
                # Whole book out to days_to_expiry_max: the gamma flip needs every
                # expiry that contributes gamma, not just the nearest one.
                if 'expiration_min' not in inspect.signature(self.client.get_options_snapshot).parameters:
                    logger.warning("Data provider does not support full_book; using single expiry")
                else:
                    today = date.today()
                    min_days = expiration_config.get('days_to_expiry_min', 0)
                    max_days = expiration_config.get('days_to_expiry_max', 30)
                    book_kwargs = {
                        'expiration_min': (today + timedelta(days=min_days)).isoformat(),
                        'expiration_max': (today + timedelta(days=max_days)).isoformat(),
                        'max_options': expiration_config.get('max_options', 40000),
                    }
                    logger.info(f"Full book: expirations {book_kwargs['expiration_min']} "
                                f"to {book_kwargs['expiration_max']}")

            if book_kwargs:
                expiration = None
            elif expiration_config.get('use_nearest_expiry', False):
                min_days = expiration_config.get('days_to_expiry_min', 0)
                max_days = expiration_config.get('days_to_expiry_max', 60)
                expiration = self.client.get_nearest_expiration(
                    symbol,
                    min_days=min_days,
                    max_days=max_days
                )

                if not expiration:
                    logger.warning(f"No suitable expiration found for {symbol}")
                    return False

                logger.info(f"Using expiration: {expiration}")
            else:
                # Get all expirations (may return a lot of data)
                expiration = None
                logger.info("Fetching all expirations (this may take a while...)")

            # Fetch options data
            options = self.client.get_options_snapshot(symbol, expiration=expiration, **book_kwargs)

            if not options:
                logger.warning(f"No options data returned for {symbol}")
                return False

            logger.info(f"Retrieved {len(options)} options for {symbol}")

            # Calculate GEX
            contract_multiplier = self.config.get_multiplier(symbol)
            symbol_gex = analyze_symbol_gex(
                symbol=symbol,
                options=options,
                underlying_price=underlying_price,
                contract_multiplier=contract_multiplier
            )

            # Save to database
            self.db.save_gex_snapshot(symbol_gex)

            logger.info(f"GEX calculation complete for {symbol}: "
                       f"Net GEX = {symbol_gex.net_gex:,.0f}")

            return True

        except Exception as e:
            logger.error(f"Error in refresh_symbol for {symbol}: {e}", exc_info=True)
            return False

    def trigger_manual_refresh(self):
        """Trigger an immediate manual refresh (non-blocking)."""
        logger.info("Manual refresh triggered")
        self.scheduler.add_job(
            func=self.refresh_all_symbols,
            trigger='date',  # Run once immediately
            id='manual_refresh',
            replace_existing=True
        )

    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get the scheduled time of the next refresh.

        Returns:
            Datetime of next scheduled run, or None if not scheduled
        """
        if self._job_id:
            job = self.scheduler.get_job(self._job_id)
            if job:
                return job.next_run_time
        return None


def run_scheduler_standalone(config_path: Optional[str] = None):
    """
    Run the scheduler as a standalone process.

    Args:
        config_path: Optional path to config file directory
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger.info("Starting GammaScope Scheduler (standalone mode)")

    try:
        # Load configuration
        config = Config()

        if config.sample_mode:
            logger.warning("Running in SAMPLE MODE - scheduler will not fetch live data")
            logger.info("Set 'sample_mode': false in config.json to enable live data")
            return

        # Initialize Alpaca client
        alpaca_client = AlpacaClient(
            api_key=config.env['ALPACA_API_KEY'],
            secret_key=config.env['ALPACA_SECRET_KEY'],
            base_url=config.env['ALPACA_BASE_URL']
        )

        # Initialize database
        db_manager = DatabaseManager()

        # Create and start scheduler
        scheduler = GEXScheduler(config, alpaca_client, db_manager)
        scheduler.start()

        logger.info("Scheduler running. Press Ctrl+C to stop.")

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")

    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        raise
    finally:
        if 'scheduler' in locals():
            scheduler.shutdown()
        logger.info("Scheduler stopped")


# Example usage
if __name__ == '__main__':
    run_scheduler_standalone()
