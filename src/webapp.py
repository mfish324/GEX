"""
Streamlit web application for GammaScope GEX monitoring dashboard.

Provides interactive UI for viewing GEX data, configuring symbols, and analyzing trends.
"""
import logging
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import Config, format_large_number
from src.models import DatabaseManager
from src.visualization import (
    plot_gex_vs_strike,
    plot_cumulative_gex,
    plot_gex_timeline,
    plot_gex_summary_table,
    create_gex_dashboard
)


logger = logging.getLogger('GammaScope.WebApp')


# Page configuration
st.set_page_config(
    page_title="GammaScope - Options Gamma Exposure Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_sample_data():
    """Load sample data for demo mode."""
    sample_data = {
        'SPY': {
            'symbol': 'SPY',
            'underlying_price': 450.25,
            'timestamp': datetime.now().isoformat(),
            'net_gex': 1250000000,
            'total_call_gex': 2100000000,
            'total_put_gex': 850000000,
            'net_dex': -450000000,
            'total_call_dex': 350000000,
            'total_put_dex': 800000000,
            'gamma_flip_point': 448.50,
            'total_call_oi': 250000,
            'total_put_oi': 180000,
            'per_strike': {
                440: {'call_gex': 150000000, 'put_gex': 80000000, 'net_gex': 70000000,
                      'call_dex': 50000000, 'put_dex': 30000000, 'net_dex': 20000000,
                      'call_oi': 15000, 'put_oi': 8000, 'total_oi': 23000},
                445: {'call_gex': 350000000, 'put_gex': 180000000, 'net_gex': 170000000,
                      'call_dex': 80000000, 'put_dex': 60000000, 'net_dex': 20000000,
                      'call_oi': 35000, 'put_oi': 18000, 'total_oi': 53000},
                450: {'call_gex': 800000000, 'put_gex': 400000000, 'net_gex': 400000000,
                      'call_dex': 150000000, 'put_dex': 120000000, 'net_dex': 30000000,
                      'call_oi': 80000, 'put_oi': 45000, 'total_oi': 125000},
                455: {'call_gex': 600000000, 'put_gex': 150000000, 'net_gex': 450000000,
                      'call_dex': 70000000, 'put_dex': 50000000, 'net_dex': 20000000,
                      'call_oi': 60000, 'put_oi': 15000, 'total_oi': 75000},
                460: {'call_gex': 200000000, 'put_gex': 40000000, 'net_gex': 160000000,
                      'call_dex': 25000000, 'put_dex': 10000000, 'net_dex': 15000000,
                      'call_oi': 20000, 'put_oi': 4000, 'total_oi': 24000},
            }
        },
        'QQQ': {
            'symbol': 'QQQ',
            'underlying_price': 380.75,
            'timestamp': datetime.now().isoformat(),
            'net_gex': -350000000,
            'total_call_gex': 450000000,
            'total_put_gex': 800000000,
            'net_dex': -120000000,
            'total_call_dex': 180000000,
            'total_put_dex': 300000000,
            'gamma_flip_point': 382.25,
            'total_call_oi': 120000,
            'total_put_oi': 200000,
            'per_strike': {
                375: {'call_gex': 80000000, 'put_gex': 150000000, 'net_gex': -70000000,
                      'call_dex': 30000000, 'put_dex': 50000000, 'net_dex': -20000000,
                      'call_oi': 10000, 'put_oi': 18000, 'total_oi': 28000},
                380: {'call_gex': 250000000, 'put_gex': 450000000, 'net_gex': -200000000,
                      'call_dex': 90000000, 'put_dex': 150000000, 'net_dex': -60000000,
                      'call_oi': 30000, 'put_oi': 55000, 'total_oi': 85000},
                385: {'call_gex': 120000000, 'put_gex': 200000000, 'net_gex': -80000000,
                      'call_dex': 60000000, 'put_dex': 100000000, 'net_dex': -40000000,
                      'call_oi': 15000, 'put_oi': 25000, 'total_oi': 40000},
            }
        }
    }
    return sample_data


def get_gex_status_emoji(net_gex: float) -> str:
    """Get emoji indicator for GEX status."""
    if net_gex > 0:
        return "🟢"  # Long gamma - stabilizing
    elif net_gex < 0:
        return "🔴"  # Short gamma - destabilizing
    else:
        return "⚪"  # Neutral


def main():
    """Main Streamlit application."""
    st.title("📊 GammaScope - Options Gamma Exposure Monitor")

    # Initialize configuration and database
    try:
        config = Config()
        db = DatabaseManager()
    except Exception as e:
        st.error(f"Configuration error: {e}")
        st.info("Please ensure .env and config.json files are properly configured.")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Mode selection
        sample_mode = config.sample_mode
        if sample_mode:
            st.warning("🔶 Running in SAMPLE MODE (demo data)")
        else:
            st.success("🟢 Live data mode")

        st.divider()

        # Symbol selection
        st.subheader("Tracked Symbols")
        symbols = config.symbols
        selected_symbol = st.selectbox(
            "Select symbol to analyze:",
            options=symbols,
            index=0 if symbols else None
        )

        st.divider()

        # Data freshness
        st.subheader("Data Status")
        refresh_interval = config.refresh_interval_minutes

        if not sample_mode:
            try:
                latest = db.get_latest_snapshot(selected_symbol)
                if latest:
                    age = datetime.now() - latest.timestamp
                    age_minutes = age.total_seconds() / 60
                    st.metric("Last Update", f"{age_minutes:.0f}m ago")
                    st.caption(f"Updates every {refresh_interval} minutes")
                else:
                    st.warning("No data available")
            except Exception as e:
                st.error(f"Database error: {e}")
        else:
            st.info("Sample data loaded")

        st.divider()

        # Manual refresh button
        if st.button("🔄 Refresh Data", disabled=sample_mode):
            st.info("Data refresh triggered (implement in scheduler)")

        # Configuration link
        st.divider()
        with st.expander("📝 Configuration"):
            st.json({
                'symbols': symbols,
                'refresh_interval': f"{refresh_interval} min",
                'sample_mode': sample_mode
            })

    # Main content area
    if not selected_symbol:
        st.warning("No symbols configured. Please update config.json")
        return

    # Load data
    if sample_mode:
        all_data = load_sample_data()
        symbol_data = all_data.get(selected_symbol)
        if not symbol_data:
            st.error(f"No sample data available for {selected_symbol}")
            return
    else:
        # Load from database
        try:
            latest_snapshot = db.get_latest_snapshot(selected_symbol)
            if not latest_snapshot:
                st.warning(f"No data available for {selected_symbol}. "
                          f"Waiting for first data refresh...")
                return

            symbol_data = latest_snapshot.to_dict()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    # Display tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Detailed Analysis", "📉 Historical", "⚙️ Config"])

    with tab1:
        show_overview(symbol_data)

    with tab2:
        show_detailed_analysis(symbol_data)

    with tab3:
        show_historical(selected_symbol, db, sample_mode)

    with tab4:
        show_configuration(config)


def show_overview(data: dict):
    """Display overview tab with summary metrics and main chart."""
    st.header(f"{data['symbol']} - GEX Overview")

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Underlying Price",
            f"${data['underlying_price']:.2f}"
        )

    with col2:
        net_gex = data['net_gex']
        status = get_gex_status_emoji(net_gex)
        st.metric(
            "Net GEX",
            format_large_number(net_gex),
            help="Positive = Long Gamma (stabilizing), Negative = Short Gamma (destabilizing)"
        )
        st.caption(f"{status} {'Long' if net_gex > 0 else 'Short'} Gamma")

    with col3:
        st.metric(
            "Call GEX",
            format_large_number(data['total_call_gex']),
            help="Total gamma exposure from call options"
        )

    with col4:
        st.metric(
            "Put GEX",
            format_large_number(data['total_put_gex']),
            help="Total gamma exposure from put options"
        )

    with col5:
        flip = data.get('gamma_flip_point')
        if flip:
            st.metric(
                "Gamma Flip",
                f"${flip:.2f}",
                help="Price where net GEX changes sign"
            )
        else:
            st.metric("Gamma Flip", "N/A")

    st.divider()

    # Main GEX chart
    st.subheader("Gamma Exposure by Strike")

    show_separate = st.checkbox("Show Calls/Puts Separately", value=False)

    try:
        fig = plot_gex_vs_strike(
            symbol=data['symbol'],
            per_strike_data=data['per_strike'],
            underlying_price=data['underlying_price'],
            gamma_flip_point=data.get('gamma_flip_point'),
            show_calls_puts_separately=show_separate,
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating chart: {e}")

    # Interpretation
    st.divider()
    st.subheader("📖 Interpretation")

    net_gex = data['net_gex']
    if net_gex > 0:
        st.success(
            f"**Positive Net GEX ({format_large_number(net_gex)})**: "
            f"Market makers are long gamma, which tends to **stabilize prices** and "
            f"**reduce volatility**. As prices move, dealers hedge by selling rallies "
            f"and buying dips."
        )
    elif net_gex < 0:
        st.error(
            f"**Negative Net GEX ({format_large_number(net_gex)})**: "
            f"Market makers are short gamma, which can **amplify price moves** and "
            f"**increase volatility**. Dealers hedge by buying rallies and selling dips, "
            f"potentially exacerbating trends."
        )
    else:
        st.info("**Neutral GEX**: Balanced gamma exposure.")


def show_detailed_analysis(data: dict):
    """Display detailed analysis tab with multiple visualizations."""
    st.header(f"{data['symbol']} - Detailed Analysis")

    # Two-column layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Cumulative GEX")
        try:
            fig_cumulative = plot_cumulative_gex(
                symbol=data['symbol'],
                per_strike_data=data['per_strike'],
                underlying_price=data['underlying_price'],
                gamma_flip_point=data.get('gamma_flip_point'),
                height=400
            )
            st.plotly_chart(fig_cumulative, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating cumulative chart: {e}")

    with col2:
        st.subheader("Open Interest Distribution")
        # Create OI chart
        strikes = sorted(data['per_strike'].keys())
        call_oi = [data['per_strike'][s]['call_oi'] for s in strikes]
        put_oi = [data['per_strike'][s]['put_oi'] for s in strikes]

        oi_df = pd.DataFrame({
            'Strike': strikes,
            'Call OI': call_oi,
            'Put OI': put_oi
        })

        st.bar_chart(oi_df.set_index('Strike'), height=400)

    st.divider()

    # Strike-level data table
    st.subheader("Strike-Level Data")

    # Convert per-strike data to DataFrame
    strike_data = []
    for strike, info in sorted(data['per_strike'].items()):
        strike_data.append({
            'Strike': f"${strike:.0f}",
            'Call GEX': format_large_number(info['call_gex']),
            'Put GEX': format_large_number(info['put_gex']),
            'Net GEX': format_large_number(info['net_gex']),
            'Call OI': f"{info['call_oi']:,}",
            'Put OI': f"{info['put_oi']:,}",
            'Total OI': f"{info['total_oi']:,}"
        })

    df = pd.DataFrame(strike_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export options
    st.divider()
    col1, col2 = st.columns([1, 4])
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{data['symbol']}_gex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    with col2:
        json_data = json.dumps(data, indent=2, default=str)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"{data['symbol']}_gex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def show_historical(symbol: str, db: DatabaseManager, sample_mode: bool):
    """Display historical trends tab."""
    st.header(f"{symbol} - Historical Trends")

    if sample_mode:
        st.info("Historical data not available in sample mode")
        return

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.slider("Days of history", min_value=1, max_value=30, value=7)

    # Fetch historical data
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        snapshots = db.get_snapshots_in_range(symbol, start_time, end_time)

        if not snapshots:
            st.warning(f"No historical data available for the last {days_back} days")
            return

        # Convert to list of dicts
        snapshot_dicts = [s.to_dict() for s in snapshots]

        # Timeline chart
        st.subheader("GEX Timeline")
        fig_timeline = plot_gex_timeline(symbol, snapshot_dicts, height=500)
        st.plotly_chart(fig_timeline, use_container_width=True)

        # Summary statistics
        st.divider()
        st.subheader("Statistics")

        df = pd.DataFrame(snapshot_dicts)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg Net GEX", format_large_number(df['net_gex'].mean()))
        with col2:
            st.metric("Max Net GEX", format_large_number(df['net_gex'].max()))
        with col3:
            st.metric("Min Net GEX", format_large_number(df['net_gex'].min()))
        with col4:
            st.metric("Std Dev", format_large_number(df['net_gex'].std()))

    except Exception as e:
        st.error(f"Error loading historical data: {e}")


def show_configuration(config: Config):
    """Display configuration management tab."""
    st.header("⚙️ Configuration")

    st.subheader("Tracked Symbols")
    st.info(f"Currently tracking: {', '.join(config.symbols)}")
    st.caption("To modify symbols, edit config.json file")

    st.divider()

    st.subheader("Refresh Settings")
    st.info(f"Data refreshes every {config.refresh_interval_minutes} minutes")
    st.caption("To change refresh interval, edit config.json file")

    st.divider()

    st.subheader("Contract Multipliers")
    multipliers = config.app.get('contract_multipliers', {})
    st.json(multipliers)

    st.divider()

    st.subheader("Environment")
    env_info = {
        'API Base URL': config.env.get('ALPACA_BASE_URL', 'Not set'),
        'API Key Set': 'Yes' if config.env.get('ALPACA_API_KEY') else 'No',
        'Debug Mode': config.env.get('DEBUG', False)
    }
    st.json(env_info)


# Run the app
if __name__ == "__main__":
    main()
