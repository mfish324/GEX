"""
Gamma Exposure (GEX) and Delta Exposure (DEX) calculation engine.

Implements industry-standard formulas for options exposure calculation,
aggregation, and gamma flip point detection.
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

import numpy as np


logger = logging.getLogger('GammaScope.GEXCalculator')


@dataclass
class OptionExposure:
    """Data class for individual option exposure metrics."""
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    gamma: float
    delta: float
    open_interest: int
    gex: float  # Gamma exposure for this option
    dex: float  # Delta exposure for this option


@dataclass
class StrikeExposure:
    """Aggregated exposure metrics for a specific strike price."""
    strike: float
    call_gex: float
    put_gex: float
    net_gex: float
    call_dex: float
    put_dex: float
    net_dex: float
    call_oi: int
    put_oi: int
    total_oi: int


@dataclass
class SymbolGEX:
    """Complete GEX analysis for a symbol."""
    symbol: str
    underlying_price: float
    timestamp: str
    total_call_gex: float
    total_put_gex: float
    net_gex: float
    total_call_dex: float
    total_put_dex: float
    net_dex: float
    gamma_flip_point: Optional[float]
    per_strike: Dict[float, StrikeExposure]
    total_call_oi: int
    total_put_oi: int


def compute_option_gex(
    option: Dict,
    underlying_price: float,
    contract_multiplier: int = 100
) -> float:
    """
    Calculate Gamma Exposure (GEX) for a single option contract.

    Formula: GEX = Gamma * OpenInterest * ContractMultiplier * UnderlyingPrice * 0.01

    The 0.01 factor converts the gamma exposure to dollar terms, as gamma measures
    the change in delta for a $1 move in the underlying.

    Args:
        option: Dictionary containing option data with keys:
            - gamma: Gamma Greek value
            - open_interest: Number of open contracts
            - type: 'call' or 'put'
        underlying_price: Current price of the underlying asset
        contract_multiplier: Number of shares per contract (default 100)

    Returns:
        GEX value in dollars. Positive for calls, negative for puts.

    Note:
        Market makers hedge by taking the opposite position, so:
        - Positive GEX (from calls) = MM is long gamma = stabilizing effect
        - Negative GEX (from puts) = MM is short gamma = destabilizing effect
    """
    gamma = option.get('gamma', 0)
    open_interest = option.get('open_interest', 0)
    option_type = option.get('type', '').lower()

    # Calculate base GEX
    gex = gamma * open_interest * contract_multiplier * underlying_price * 0.01

    # Convention: puts contribute negative GEX
    if option_type == 'put':
        gex = -gex

    return gex


def compute_option_dex(
    option: Dict,
    underlying_price: float,
    contract_multiplier: int = 100
) -> float:
    """
    Calculate Delta Exposure (DEX) for a single option contract.

    Formula: DEX = Delta * OpenInterest * ContractMultiplier * UnderlyingPrice

    Args:
        option: Dictionary containing option data with keys:
            - delta: Delta Greek value
            - open_interest: Number of open contracts
            - type: 'call' or 'put'
        underlying_price: Current price of the underlying asset
        contract_multiplier: Number of shares per contract (default 100)

    Returns:
        DEX value in dollars
    """
    delta = option.get('delta', 0)
    open_interest = option.get('open_interest', 0)
    option_type = option.get('type', '').lower()

    # Calculate DEX
    dex = delta * open_interest * contract_multiplier * underlying_price

    # Puts have negative delta, which is already reflected in the delta value
    if option_type == 'put':
        dex = -dex

    return dex


def aggregate_gex(
    options: List[Dict],
    underlying_price: float,
    contract_multiplier: int = 100
) -> Dict:
    """
    Aggregate GEX and DEX across all options, computing totals and per-strike breakdown.

    Args:
        options: List of option dictionaries
        underlying_price: Current price of the underlying
        contract_multiplier: Number of shares per contract (default 100)

    Returns:
        Dictionary containing:
            - total_call_gex: Total GEX from call options
            - total_put_gex: Total GEX from put options (absolute value)
            - net_gex: Net GEX (call - put)
            - total_call_dex: Total DEX from call options
            - total_put_dex: Total DEX from put options
            - net_dex: Net DEX
            - per_strike: Dict mapping strike -> {call_gex, put_gex, net_gex, call_dex, put_dex, net_dex, call_oi, put_oi}
            - total_call_oi: Total open interest in calls
            - total_put_oi: Total open interest in puts
    """
    # Initialize accumulators
    total_call_gex = 0.0
    total_put_gex = 0.0
    total_call_dex = 0.0
    total_put_dex = 0.0
    total_call_oi = 0
    total_put_oi = 0

    # Per-strike breakdown
    per_strike = defaultdict(lambda: {
        'call_gex': 0.0, 'put_gex': 0.0,
        'call_dex': 0.0, 'put_dex': 0.0,
        'call_oi': 0, 'put_oi': 0
    })

    # Process each option
    for option in options:
        strike = option.get('strike', 0)
        option_type = option.get('type', '').lower()
        oi = option.get('open_interest', 0)

        # Calculate GEX and DEX
        gex = compute_option_gex(option, underlying_price, contract_multiplier)
        dex = compute_option_dex(option, underlying_price, contract_multiplier)

        # Accumulate totals
        if option_type == 'call':
            total_call_gex += gex
            total_call_dex += dex
            total_call_oi += oi
            per_strike[strike]['call_gex'] += gex
            per_strike[strike]['call_dex'] += dex
            per_strike[strike]['call_oi'] += oi
        elif option_type == 'put':
            # GEX for puts is already negative from compute_option_gex
            total_put_gex += abs(gex)  # Store absolute value
            total_put_dex += abs(dex)
            total_put_oi += oi
            per_strike[strike]['put_gex'] += abs(gex)
            per_strike[strike]['put_dex'] += abs(dex)
            per_strike[strike]['put_oi'] += oi

    # Calculate net GEX (calls positive, puts negative)
    net_gex = total_call_gex - total_put_gex
    net_dex = total_call_dex - total_put_dex

    # Calculate net GEX per strike
    for strike, data in per_strike.items():
        data['net_gex'] = data['call_gex'] - data['put_gex']
        data['net_dex'] = data['call_dex'] - data['put_dex']
        data['total_oi'] = data['call_oi'] + data['put_oi']

    result = {
        'total_call_gex': total_call_gex,
        'total_put_gex': total_put_gex,
        'net_gex': net_gex,
        'total_call_dex': total_call_dex,
        'total_put_dex': total_put_dex,
        'net_dex': net_dex,
        'per_strike': dict(per_strike),
        'total_call_oi': total_call_oi,
        'total_put_oi': total_put_oi,
    }

    logger.info(f"Aggregated GEX: Net={net_gex:,.0f}, Calls={total_call_gex:,.0f}, Puts={total_put_gex:,.0f}")

    return result


# Only zero crossings within this fraction of spot count as a gamma flip.
FLIP_WINDOW_PCT = 0.20


def find_gamma_flip_point(per_strike_net_gex: Dict[float, float], underlying_price: float) -> Optional[float]:
    """
    Find the gamma flip point where net GEX crosses zero.

    The gamma flip point is the price level where market maker positioning
    changes from long gamma (stabilizing) to short gamma (destabilizing) or vice versa.

    Args:
        per_strike_net_gex: Dictionary mapping strike prices to net GEX values
        underlying_price: Current underlying price (for context)

    Returns:
        Estimated flip point price, or None if not found

    Algorithm:
        1. Sort strikes and net GEX values
        2. Look for sign change in net GEX
        3. Use linear interpolation to estimate exact flip point
        4. Keep crossings within FLIP_WINDOW_PCT of spot; return the nearest to spot
    """
    if not per_strike_net_gex:
        return None

    # Convert to sorted lists
    strikes = sorted(per_strike_net_gex.keys())
    net_gex_values = [per_strike_net_gex[s] for s in strikes]

    # Collect every zero crossing within a window around spot. Deep-OTM strikes
    # have near-zero net GEX whose sign is set by a few stray contracts, so a
    # crossing far from spot is noise (e.g. SPY "flip" at 449 with spot at 772).
    lo = underlying_price * (1 - FLIP_WINDOW_PCT)
    hi = underlying_price * (1 + FLIP_WINDOW_PCT)
    crossings = []
    for i in range(len(net_gex_values) - 1):
        current_gex = net_gex_values[i]
        next_gex = net_gex_values[i + 1]

        if (current_gex > 0 and next_gex < 0) or (current_gex < 0 and next_gex > 0):
            current_strike = strikes[i]
            next_strike = strikes[i + 1]
            ratio = -current_gex / (next_gex - current_gex)
            flip_point = current_strike + ratio * (next_strike - current_strike)
            if lo <= flip_point <= hi:
                crossings.append(flip_point)

    if crossings:
        # Several crossings are possible; the one nearest spot is the relevant level.
        flip_point = min(crossings, key=lambda f: abs(f - underlying_price))
        logger.info(f"Gamma flip point found: ${flip_point:.2f} "
                    f"({len(crossings)} crossing(s) within {FLIP_WINDOW_PCT:.0%} of spot)")
        return flip_point

    # No flip point found
    logger.info("No gamma flip point detected in current strike range")
    return None


def analyze_symbol_gex(
    symbol: str,
    options: List[Dict],
    underlying_price: float,
    contract_multiplier: int = 100,
    timestamp: Optional[str] = None
) -> SymbolGEX:
    """
    Perform complete GEX analysis for a symbol.

    Args:
        symbol: Ticker symbol
        options: List of option data dictionaries
        underlying_price: Current underlying price
        contract_multiplier: Contract multiplier (default 100)
        timestamp: Timestamp of analysis (defaults to now)

    Returns:
        SymbolGEX object with complete analysis
    """
    from datetime import datetime

    if timestamp is None:
        timestamp = datetime.now().isoformat()

    # Aggregate GEX across all options
    agg = aggregate_gex(options, underlying_price, contract_multiplier)

    # Extract per-strike net GEX for flip point calculation
    per_strike_net_gex = {
        strike: data['net_gex']
        for strike, data in agg['per_strike'].items()
    }

    # Find gamma flip point
    flip_point = find_gamma_flip_point(per_strike_net_gex, underlying_price)

    # Create StrikeExposure objects
    strike_exposures = {}
    for strike, data in agg['per_strike'].items():
        strike_exposures[strike] = StrikeExposure(
            strike=strike,
            call_gex=data['call_gex'],
            put_gex=data['put_gex'],
            net_gex=data['net_gex'],
            call_dex=data['call_dex'],
            put_dex=data['put_dex'],
            net_dex=data['net_dex'],
            call_oi=data['call_oi'],
            put_oi=data['put_oi'],
            total_oi=data['total_oi']
        )

    # Build final result
    result = SymbolGEX(
        symbol=symbol,
        underlying_price=underlying_price,
        timestamp=timestamp,
        total_call_gex=agg['total_call_gex'],
        total_put_gex=agg['total_put_gex'],
        net_gex=agg['net_gex'],
        total_call_dex=agg['total_call_dex'],
        total_put_dex=agg['total_put_dex'],
        net_dex=agg['net_dex'],
        gamma_flip_point=flip_point,
        per_strike=strike_exposures,
        total_call_oi=agg['total_call_oi'],
        total_put_oi=agg['total_put_oi']
    )

    flip_str = f"${flip_point:.2f}" if flip_point is not None else "N/A"
    logger.info(f"GEX analysis complete for {symbol}: "
               f"Net GEX={result.net_gex:,.0f}, Flip={flip_str}")

    return result


def get_gex_interpretation(net_gex: float) -> str:
    """
    Get human-readable interpretation of net GEX value.

    Args:
        net_gex: Net gamma exposure value

    Returns:
        Interpretation string
    """
    if net_gex > 0:
        return "Positive GEX: Market makers long gamma → Price stabilizing (reduced volatility)"
    elif net_gex < 0:
        return "Negative GEX: Market makers short gamma → Price destabilizing (increased volatility)"
    else:
        return "Neutral GEX: Balanced gamma exposure"


# Example usage and testing
if __name__ == '__main__':
    # Sample test data
    sample_options = [
        # Calls
        {'symbol': 'SPY230120C00400000', 'strike': 400, 'type': 'call',
         'gamma': 0.005, 'delta': 0.50, 'open_interest': 10000, 'expiration': '2023-01-20'},
        {'symbol': 'SPY230120C00410000', 'strike': 410, 'type': 'call',
         'gamma': 0.004, 'delta': 0.40, 'open_interest': 8000, 'expiration': '2023-01-20'},
        # Puts
        {'symbol': 'SPY230120P00390000', 'strike': 390, 'type': 'put',
         'gamma': 0.006, 'delta': -0.45, 'open_interest': 12000, 'expiration': '2023-01-20'},
        {'symbol': 'SPY230120P00380000', 'strike': 380, 'type': 'put',
         'gamma': 0.005, 'delta': -0.35, 'open_interest': 9000, 'expiration': '2023-01-20'},
    ]

    underlying_price = 400.0

    print("Testing GEX Calculator\n" + "="*50)

    # Test individual option GEX
    print("\n1. Individual Option GEX:")
    for opt in sample_options[:2]:
        gex = compute_option_gex(opt, underlying_price)
        print(f"  {opt['type'].upper()} @ ${opt['strike']}: GEX = ${gex:,.2f}")

    # Test aggregation
    print("\n2. Aggregated GEX:")
    agg = aggregate_gex(sample_options, underlying_price)
    print(f"  Total Call GEX: ${agg['total_call_gex']:,.2f}")
    print(f"  Total Put GEX:  ${agg['total_put_gex']:,.2f}")
    print(f"  Net GEX:        ${agg['net_gex']:,.2f}")
    print(f"  {get_gex_interpretation(agg['net_gex'])}")

    # Test full analysis
    print("\n3. Full Symbol Analysis:")
    analysis = analyze_symbol_gex('SPY', sample_options, underlying_price)
    print(f"  Symbol: {analysis.symbol}")
    print(f"  Underlying: ${analysis.underlying_price:.2f}")
    print(f"  Net GEX: ${analysis.net_gex:,.2f}")
    print(f"  Gamma Flip Point: ${analysis.gamma_flip_point:.2f}" if analysis.gamma_flip_point else "  No flip point")
    print(f"  Number of strikes: {len(analysis.per_strike)}")
