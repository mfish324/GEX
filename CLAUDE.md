# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GammaScope is a Python application for monitoring Options Gamma Exposure (GEX) across equity symbols. It fetches options data from market data providers (Polygon.io or Alpaca), calculates gamma/delta exposure metrics, and displays them in a Streamlit dashboard.

## Common Commands

```bash
# Run full system (scheduler + webapp)
python main.py

# Run webapp only (requires existing data in SQLite)
python main.py --webapp

# Run scheduler only (background data refresh)
python main.py --scheduler

# Fetch data once and exit
python main.py --once

# Run with debug logging
python main.py --debug

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Test individual module
python -m src.gex_calculator
python -m src.alpaca_client
python -m src.models
```

## Architecture

### Entry Point
- `main.py` - CLI entry point handling mode selection (scheduler, webapp, or both)

### Core Modules (src/)
- `gex_calculator.py` - GEX/DEX computation engine with dataclasses (`OptionExposure`, `StrikeExposure`, `SymbolGEX`). Key functions: `compute_option_gex()`, `aggregate_gex()`, `find_gamma_flip_point()`, `analyze_symbol_gex()`
- `alpaca_client.py` - Alpaca API wrapper with rate limiting and retry logic
- `polygon_client.py` - Polygon.io API wrapper (alternative data provider)
- `models.py` - SQLAlchemy models (`GEXSnapshot`, `OptionContract`, `RefreshLog`) and `DatabaseManager` class
- `scheduler.py` - APScheduler-based periodic data refresh via `GEXScheduler` class
- `webapp.py` - Streamlit dashboard with Overview, Detailed Analysis, Historical, and Config tabs
- `visualization.py` - Plotly chart builders
- `utils.py` - Configuration loading (`Config` singleton), environment/JSON config, helpers

### Data Flow
1. Scheduler triggers refresh at configured interval
2. Data client (Alpaca/Polygon) fetches underlying price and options chain with Greeks
3. `gex_calculator.analyze_symbol_gex()` computes GEX metrics and finds gamma flip point
4. `DatabaseManager.save_gex_snapshot()` persists to SQLite (`data/cache.db`)
5. Webapp reads from database and renders Plotly charts

### Configuration
- `.env` - API credentials and `DATA_PROVIDER` selection (polygon or alpaca)
- `config.json` - Symbols, refresh interval, contract multipliers, sample_mode, expiration filters

### GEX Formula
```
GEX = Gamma * OpenInterest * ContractMultiplier * UnderlyingPrice * 0.01
```
Calls contribute positive GEX, puts contribute negative GEX. Net GEX indicates market maker gamma positioning.

## Testing

Tests are in `tests/` using pytest. The test suite covers GEX calculations, aggregation, and flip point detection. Use `pytest.mark.slow` and `pytest.mark.integration` markers for selective test runs.

## Key Dependencies
- `alpaca-py` / `polygon` - Market data APIs
- `streamlit` - Web dashboard
- `sqlalchemy` - Database ORM
- `apscheduler` - Background job scheduling
- `plotly` - Interactive charts
