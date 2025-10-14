"""
Plotly-based visualization components for GEX data.

Creates interactive charts for gamma exposure analysis, including:
- GEX vs Strike distribution
- Cumulative GEX curves
- Historical GEX trends
- Call/Put breakdowns
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


logger = logging.getLogger('GammaScope.Visualization')


def plot_gex_vs_strike(
    symbol: str,
    per_strike_data: Dict[float, Dict],
    underlying_price: float,
    gamma_flip_point: Optional[float] = None,
    show_calls_puts_separately: bool = False,
    height: int = 600
) -> go.Figure:
    """
    Create a bar chart showing GEX distribution across strikes.

    Args:
        symbol: Ticker symbol
        per_strike_data: Dictionary mapping strike -> {call_gex, put_gex, net_gex, ...}
        underlying_price: Current underlying price
        gamma_flip_point: Gamma flip point price (optional)
        show_calls_puts_separately: If True, show call and put GEX separately
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Sort strikes
    strikes = sorted(per_strike_data.keys())

    if show_calls_puts_separately:
        # Separate call and put GEX
        call_gex = [per_strike_data[s]['call_gex'] for s in strikes]
        put_gex = [-per_strike_data[s]['put_gex'] for s in strikes]  # Negative for visual separation

        fig = go.Figure()

        # Add call GEX bars
        fig.add_trace(go.Bar(
            x=strikes,
            y=call_gex,
            name='Call GEX',
            marker_color='green',
            hovertemplate='<b>Strike: $%{x:.0f}</b><br>Call GEX: $%{y:,.0f}<extra></extra>'
        ))

        # Add put GEX bars
        fig.add_trace(go.Bar(
            x=strikes,
            y=put_gex,
            name='Put GEX',
            marker_color='red',
            hovertemplate='<b>Strike: $%{x:.0f}</b><br>Put GEX: $%{y:,.0f}<extra></extra>'
        ))

        yaxis_title = 'GEX (Calls: +, Puts: -)'
    else:
        # Net GEX
        net_gex = [per_strike_data[s]['net_gex'] for s in strikes]
        colors = ['green' if gex >= 0 else 'red' for gex in net_gex]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=strikes,
            y=net_gex,
            name='Net GEX',
            marker_color=colors,
            hovertemplate='<b>Strike: $%{x:.0f}</b><br>Net GEX: $%{y:,.0f}<extra></extra>'
        ))

        yaxis_title = 'Net GEX ($)'

    # Add vertical line for current price
    fig.add_vline(
        x=underlying_price,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Current: ${underlying_price:.2f}",
        annotation_position="top"
    )

    # Add vertical line for gamma flip point
    if gamma_flip_point:
        fig.add_vline(
            x=gamma_flip_point,
            line_dash="dot",
            line_color="orange",
            annotation_text=f"Flip: ${gamma_flip_point:.2f}",
            annotation_position="bottom"
        )

    # Update layout
    fig.update_layout(
        title=f'{symbol} Gamma Exposure by Strike',
        xaxis_title='Strike Price ($)',
        yaxis_title=yaxis_title,
        height=height,
        hovermode='x unified',
        showlegend=True,
        template='plotly_white'
    )

    return fig


def plot_cumulative_gex(
    symbol: str,
    per_strike_data: Dict[float, Dict],
    underlying_price: float,
    gamma_flip_point: Optional[float] = None,
    height: int = 600
) -> go.Figure:
    """
    Create a cumulative GEX curve showing total exposure above/below each strike.

    Args:
        symbol: Ticker symbol
        per_strike_data: Dictionary mapping strike -> {net_gex, ...}
        underlying_price: Current underlying price
        gamma_flip_point: Gamma flip point price (optional)
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Sort strikes
    strikes = sorted(per_strike_data.keys())
    net_gex = [per_strike_data[s]['net_gex'] for s in strikes]

    # Calculate cumulative GEX
    cumulative_gex = np.cumsum(net_gex)

    fig = go.Figure()

    # Add cumulative GEX line
    fig.add_trace(go.Scatter(
        x=strikes,
        y=cumulative_gex,
        mode='lines+markers',
        name='Cumulative GEX',
        line=dict(color='purple', width=2),
        marker=dict(size=4),
        hovertemplate='<b>Strike: $%{x:.0f}</b><br>Cumulative GEX: $%{y:,.0f}<extra></extra>'
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add vertical line for current price
    fig.add_vline(
        x=underlying_price,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Current: ${underlying_price:.2f}",
        annotation_position="top"
    )

    # Add vertical line for gamma flip point
    if gamma_flip_point:
        fig.add_vline(
            x=gamma_flip_point,
            line_dash="dot",
            line_color="orange",
            annotation_text=f"Flip: ${gamma_flip_point:.2f}",
            annotation_position="bottom"
        )

    # Update layout
    fig.update_layout(
        title=f'{symbol} Cumulative Gamma Exposure',
        xaxis_title='Strike Price ($)',
        yaxis_title='Cumulative GEX ($)',
        height=height,
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


def plot_gex_timeline(
    symbol: str,
    snapshots: List[Dict],
    height: int = 400
) -> go.Figure:
    """
    Create a timeline chart showing historical GEX evolution.

    Args:
        symbol: Ticker symbol
        snapshots: List of snapshot dictionaries with 'timestamp' and GEX fields
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    if not snapshots:
        # Return empty figure
        fig = go.Figure()
        fig.update_layout(
            title=f'{symbol} GEX Timeline (No Data)',
            height=height,
            template='plotly_white'
        )
        return fig

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(snapshots)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(f'{symbol} Net GEX Over Time', 'Underlying Price'),
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4]
    )

    # Net GEX line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['net_gex'],
            mode='lines+markers',
            name='Net GEX',
            line=dict(color='purple', width=2),
            marker=dict(size=4),
            hovertemplate='<b>%{x}</b><br>Net GEX: $%{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Add zero line for GEX
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)

    # Underlying price
    if 'underlying_price' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['underlying_price'],
                mode='lines',
                name='Underlying Price',
                line=dict(color='blue', width=2),
                hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

    # Update layout
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Net GEX ($)", row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)

    fig.update_layout(
        height=height,
        hovermode='x unified',
        showlegend=True,
        template='plotly_white'
    )

    return fig


def plot_gex_heatmap(
    symbol: str,
    per_strike_data: Dict[float, Dict],
    underlying_price: float,
    height: int = 600
) -> go.Figure:
    """
    Create a heatmap showing call vs put GEX across strikes.

    Args:
        symbol: Ticker symbol
        per_strike_data: Dictionary mapping strike -> {call_gex, put_gex, ...}
        underlying_price: Current underlying price
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    strikes = sorted(per_strike_data.keys())
    call_gex = [per_strike_data[s]['call_gex'] for s in strikes]
    put_gex = [per_strike_data[s]['put_gex'] for s in strikes]

    fig = go.Figure()

    # Add call GEX trace
    fig.add_trace(go.Bar(
        x=strikes,
        y=call_gex,
        name='Call GEX',
        marker_color='rgba(0, 255, 0, 0.6)',
        yaxis='y',
        offsetgroup=1
    ))

    # Add put GEX trace
    fig.add_trace(go.Bar(
        x=strikes,
        y=put_gex,
        name='Put GEX',
        marker_color='rgba(255, 0, 0, 0.6)',
        yaxis='y',
        offsetgroup=2
    ))

    # Add current price line
    fig.add_vline(
        x=underlying_price,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Current: ${underlying_price:.2f}"
    )

    fig.update_layout(
        title=f'{symbol} Call vs Put Gamma Exposure',
        xaxis_title='Strike Price ($)',
        yaxis_title='GEX ($)',
        height=height,
        barmode='group',
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


def plot_gex_summary_table(symbols_gex: List[Dict]) -> go.Figure:
    """
    Create a summary table showing GEX metrics for multiple symbols.

    Args:
        symbols_gex: List of dictionaries with GEX summary data

    Returns:
        Plotly Figure object with table
    """
    if not symbols_gex:
        return go.Figure()

    # Prepare table data
    headers = ['Symbol', 'Price', 'Net GEX', 'Call GEX', 'Put GEX', 'Flip Point', 'Status']

    symbol_col = [d['symbol'] for d in symbols_gex]
    price_col = [f"${d.get('underlying_price', 0):.2f}" for d in symbols_gex]
    net_gex_col = [f"${d.get('net_gex', 0):,.0f}" for d in symbols_gex]
    call_gex_col = [f"${d.get('total_call_gex', 0):,.0f}" for d in symbols_gex]
    put_gex_col = [f"${d.get('total_put_gex', 0):,.0f}" for d in symbols_gex]
    flip_col = [f"${d.get('gamma_flip_point', 0):.2f}" if d.get('gamma_flip_point') else 'N/A'
                for d in symbols_gex]

    # Determine status
    status_col = []
    for d in symbols_gex:
        net = d.get('net_gex', 0)
        if net > 0:
            status_col.append('🟢 Long Gamma')
        elif net < 0:
            status_col.append('🔴 Short Gamma')
        else:
            status_col.append('⚪ Neutral')

    # Create table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=headers,
            fill_color='paleturquoise',
            align='left',
            font=dict(size=12, color='black')
        ),
        cells=dict(
            values=[symbol_col, price_col, net_gex_col, call_gex_col, put_gex_col, flip_col, status_col],
            fill_color='lavender',
            align='left',
            font=dict(size=11)
        )
    )])

    fig.update_layout(
        title='GEX Summary',
        height=min(400, 150 + len(symbols_gex) * 30)
    )

    return fig


def create_gex_dashboard(
    symbol: str,
    symbol_gex_data: Dict,
    height_per_chart: int = 500
) -> go.Figure:
    """
    Create a comprehensive dashboard with multiple GEX visualizations.

    Args:
        symbol: Ticker symbol
        symbol_gex_data: Dictionary with GEX analysis data
        height_per_chart: Height of each chart in pixels

    Returns:
        Plotly Figure with subplots
    """
    per_strike = symbol_gex_data.get('per_strike', {})
    underlying_price = symbol_gex_data.get('underlying_price', 0)
    gamma_flip = symbol_gex_data.get('gamma_flip_point')

    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Net GEX by Strike',
            'Call vs Put GEX',
            'Cumulative GEX',
            'GEX Interpretation'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "table"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    # Prepare data
    strikes = sorted(per_strike.keys())
    net_gex = [per_strike[s]['net_gex'] for s in strikes]
    call_gex = [per_strike[s]['call_gex'] for s in strikes]
    put_gex = [per_strike[s]['put_gex'] for s in strikes]
    cumulative = np.cumsum(net_gex)

    # 1. Net GEX bars
    colors = ['green' if g >= 0 else 'red' for g in net_gex]
    fig.add_trace(
        go.Bar(x=strikes, y=net_gex, marker_color=colors, name='Net GEX', showlegend=False),
        row=1, col=1
    )

    # 2. Call vs Put
    fig.add_trace(
        go.Bar(x=strikes, y=call_gex, name='Calls', marker_color='green'),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=strikes, y=put_gex, name='Puts', marker_color='red'),
        row=1, col=2
    )

    # 3. Cumulative GEX
    fig.add_trace(
        go.Scatter(x=strikes, y=cumulative, mode='lines+markers',
                   line=dict(color='purple'), name='Cumulative', showlegend=False),
        row=2, col=1
    )

    # 4. Summary table
    summary_data = [
        ['Net GEX', f"${symbol_gex_data.get('net_gex', 0):,.0f}"],
        ['Call GEX', f"${symbol_gex_data.get('total_call_gex', 0):,.0f}"],
        ['Put GEX', f"${symbol_gex_data.get('total_put_gex', 0):,.0f}"],
        ['Flip Point', f"${gamma_flip:.2f}" if gamma_flip else 'N/A'],
        ['Underlying', f"${underlying_price:.2f}"]
    ]

    fig.add_trace(
        go.Table(
            header=dict(values=['Metric', 'Value'], fill_color='paleturquoise'),
            cells=dict(values=[[r[0] for r in summary_data], [r[1] for r in summary_data]],
                      fill_color='lavender')
        ),
        row=2, col=2
    )

    # Update layout
    total_height = height_per_chart * 2
    fig.update_layout(
        title_text=f"{symbol} Gamma Exposure Dashboard",
        height=total_height,
        showlegend=True,
        template='plotly_white'
    )

    return fig


# Example usage
if __name__ == '__main__':
    # Sample data for testing
    sample_per_strike = {
        390: {'call_gex': 500000, 'put_gex': 300000, 'net_gex': 200000, 'call_oi': 1000, 'put_oi': 800},
        395: {'call_gex': 800000, 'put_gex': 400000, 'net_gex': 400000, 'call_oi': 1500, 'put_oi': 900},
        400: {'call_gex': 1200000, 'put_gex': 1000000, 'net_gex': 200000, 'call_oi': 2000, 'put_oi': 1800},
        405: {'call_gex': 600000, 'put_gex': 1200000, 'net_gex': -600000, 'call_oi': 1200, 'put_oi': 2500},
        410: {'call_gex': 300000, 'put_gex': 800000, 'net_gex': -500000, 'call_oi': 800, 'put_oi': 1500},
    }

    underlying = 400.0
    flip = 402.5

    # Test visualization
    fig = plot_gex_vs_strike('SPY', sample_per_strike, underlying, flip)
    print("Created GEX vs Strike chart")
    # fig.show()  # Uncomment to display
