"""
GammaScope - Main entry point

Runs the complete GEX monitoring system with scheduler and web dashboard.

Usage:
    python main.py              # Run full system (scheduler + webapp)
    python main.py --scheduler  # Run scheduler only (background data refresh)
    python main.py --webapp     # Run webapp only (requires existing data)
    python main.py --once       # Fetch data once and exit
"""
import argparse
import logging
import sys
import time
from pathlib import Path
from threading import Thread

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils import Config, setup_logging
from src.models import DatabaseManager
from src.scheduler import GEXScheduler


logger = logging.getLogger('GammaScope.Main')


def create_data_client(config: Config):
    """
    Create the appropriate data client based on configuration.

    Args:
        config: Configuration object

    Returns:
        AlpacaClient or PolygonClient instance
    """
    provider = config.env.get('DATA_PROVIDER', 'polygon').lower()

    if provider == 'alpaca':
        from src.alpaca_client import AlpacaClient
        logger.info("Using Alpaca as data provider")
        return AlpacaClient(
            api_key=config.env['ALPACA_API_KEY'],
            secret_key=config.env['ALPACA_SECRET_KEY'],
            base_url=config.env['ALPACA_BASE_URL']
        )
    elif provider == 'polygon':
        from src.polygon_client import PolygonClient
        logger.info("Using Polygon.io as data provider")
        return PolygonClient(
            api_key=config.env['POLYGON_API_KEY'],
            min_request_interval=config.app.get('polygon_request_interval_seconds', 12.0)
        )
    else:
        raise ValueError(f"Unknown data provider: {provider}")


def run_scheduler(config: Config):
    """
    Run the data refresh scheduler.

    Args:
        config: Configuration object
    """
    logger.info("Starting scheduler...")

    if config.sample_mode:
        logger.warning("⚠️  SAMPLE MODE enabled - scheduler will not fetch live data")
        logger.info("Set 'sample_mode': false in config.json to enable live data fetching")
        logger.info("You can still run the webapp to view sample data")
        return

    try:
        # Initialize data client (Alpaca or Polygon)
        data_client = create_data_client(config)

        # Initialize database
        db_manager = DatabaseManager()

        # Create and start scheduler
        scheduler = GEXScheduler(config, data_client, db_manager)
        scheduler.start()

        logger.info("✓ Scheduler started successfully")
        logger.info(f"  Tracking symbols: {', '.join(config.symbols)}")
        logger.info(f"  Refresh interval: {config.refresh_interval_minutes} minutes")

        next_run = scheduler.get_next_run_time()
        if next_run:
            logger.info(f"  Next refresh: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        return scheduler

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        sys.exit(1)


def run_webapp():
    """
    Run the Streamlit web application.

    This will start the Streamlit server in the current process.
    """
    logger.info("Starting web application...")

    try:
        import streamlit.web.cli as stcli
        from streamlit.runtime import exists

        webapp_path = str(Path(__file__).parent / 'src' / 'webapp.py')

        # Check if file exists
        if not Path(webapp_path).exists():
            logger.error(f"Webapp file not found: {webapp_path}")
            sys.exit(1)

        logger.info(f"Launching Streamlit app: {webapp_path}")

        # Run Streamlit
        sys.argv = [
            "streamlit",
            "run",
            webapp_path,
            "--server.headless=true",
            "--server.address=0.0.0.0",
            "--server.port=8501",
            "--browser.gatherUsageStats=false"
        ]

        sys.exit(stcli.main())

    except ImportError:
        logger.error("Streamlit not installed. Please run: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start webapp: {e}", exc_info=True)
        sys.exit(1)


def run_once(config: Config):
    """
    Fetch GEX data once and exit (useful for testing or cron jobs).

    Args:
        config: Configuration object
    """
    logger.info("Running single data fetch...")

    if config.sample_mode:
        logger.error("Cannot run single fetch in sample mode")
        logger.info("Set 'sample_mode': false in config.json")
        sys.exit(1)

    try:
        # Initialize data client (Alpaca or Polygon)
        data_client = create_data_client(config)
        db_manager = DatabaseManager()

        # Create scheduler (but don't start it)
        scheduler = GEXScheduler(config, data_client, db_manager)

        # Run refresh once
        logger.info(f"Fetching data for: {', '.join(config.symbols)}")
        scheduler.refresh_all_symbols()

        logger.info("✓ Data fetch complete")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Data fetch failed: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='GammaScope - Options Gamma Exposure Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                 Run scheduler + webapp (full system)
  python main.py --scheduler     Run scheduler only (background process)
  python main.py --webapp        Run webapp only (requires existing data)
  python main.py --once          Fetch data once and exit
  python main.py --debug         Run with debug logging

For sample/demo mode, set "sample_mode": true in config.json
        """
    )

    parser.add_argument(
        '--scheduler',
        action='store_true',
        help='Run scheduler only (without webapp)'
    )
    parser.add_argument(
        '--webapp',
        action='store_true',
        help='Run webapp only (without scheduler)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Fetch data once and exit (no continuous refresh)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = Config()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please ensure .env and config.json files are properly configured")
        print("See .env.example for required environment variables")
        sys.exit(1)

    # Set up logging
    log_level = logging.DEBUG if (args.debug or config.env.get('DEBUG')) else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger.info("=" * 60)
    logger.info("GammaScope - Options Gamma Exposure Monitor")
    logger.info("=" * 60)
    logger.info(f"Data provider: {config.env.get('DATA_PROVIDER', 'polygon').upper()}")
    logger.info(f"Tracking symbols: {', '.join(config.symbols)}")
    logger.info(f"Refresh interval: {config.refresh_interval_minutes} minutes")
    logger.info(f"Sample mode: {'ON' if config.sample_mode else 'OFF'}")
    logger.info("=" * 60)

    # Determine mode
    if args.once:
        # Single fetch mode
        run_once(config)

    elif args.scheduler and not args.webapp:
        # Scheduler only
        scheduler = run_scheduler(config)

        if scheduler:
            logger.info("Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                scheduler.shutdown()
                logger.info("Scheduler stopped")

    elif args.webapp and not args.scheduler:
        # Webapp only
        logger.info("Starting webapp only (scheduler disabled)")
        run_webapp()

    else:
        # Default: Run both scheduler and webapp
        logger.info("Starting full system (scheduler + webapp)")

        # Start scheduler in background thread
        scheduler = None
        if not config.sample_mode:
            scheduler = run_scheduler(config)

            if not scheduler:
                logger.error("Failed to start scheduler")
                sys.exit(1)
        else:
            logger.info("Sample mode: skipping scheduler startup")

        # Start webapp (this will block)
        logger.info("Starting webapp...")
        logger.info("Once the webapp starts, open your browser to: http://localhost:8501")

        try:
            run_webapp()
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            if scheduler:
                scheduler.shutdown()
            logger.info("GammaScope stopped")


if __name__ == '__main__':
    main()
