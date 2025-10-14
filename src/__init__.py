"""
GammaScope - Options Gamma Exposure Monitoring System

A comprehensive tool for tracking and analyzing options gamma exposure (GEX)
across multiple symbols using real-time data from Alpaca Markets API.
"""

__version__ = '1.0.0'
__author__ = 'GammaScope Team'

from .alpaca_client import AlpacaClient
from .gex_calculator import (
    compute_option_gex,
    compute_option_dex,
    aggregate_gex,
    find_gamma_flip_point,
    analyze_symbol_gex,
    SymbolGEX,
    StrikeExposure,
    OptionExposure
)
from .models import DatabaseManager, GEXSnapshot
from .scheduler import GEXScheduler
from .utils import Config, format_large_number
from .visualization import (
    plot_gex_vs_strike,
    plot_cumulative_gex,
    plot_gex_timeline,
    plot_gex_summary_table,
    create_gex_dashboard
)

__all__ = [
    'AlpacaClient',
    'compute_option_gex',
    'compute_option_dex',
    'aggregate_gex',
    'find_gamma_flip_point',
    'analyze_symbol_gex',
    'SymbolGEX',
    'StrikeExposure',
    'OptionExposure',
    'DatabaseManager',
    'GEXSnapshot',
    'GEXScheduler',
    'Config',
    'format_large_number',
    'plot_gex_vs_strike',
    'plot_cumulative_gex',
    'plot_gex_timeline',
    'plot_gex_summary_table',
    'create_gex_dashboard',
]
