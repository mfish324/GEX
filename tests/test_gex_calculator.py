"""
Unit tests for GEX calculation engine.
"""
import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from gex_calculator import (
    compute_option_gex,
    compute_option_dex,
    aggregate_gex,
    find_gamma_flip_point,
    analyze_symbol_gex,
    get_gex_interpretation
)


class TestComputeOptionGEX:
    """Test suite for individual option GEX calculation."""

    def test_call_option_gex(self):
        """Test GEX calculation for a call option."""
        option = {
            'type': 'call',
            'gamma': 0.005,
            'open_interest': 10000,
            'strike': 400
        }
        underlying_price = 400.0
        contract_multiplier = 100

        gex = compute_option_gex(option, underlying_price, contract_multiplier)

        # Expected: 0.005 * 10000 * 100 * 400 * 0.01 = 2,000,000
        expected = 0.005 * 10000 * 100 * 400 * 0.01
        assert gex == pytest.approx(expected)
        assert gex > 0  # Calls have positive GEX

    def test_put_option_gex(self):
        """Test GEX calculation for a put option."""
        option = {
            'type': 'put',
            'gamma': 0.006,
            'open_interest': 12000,
            'strike': 390
        }
        underlying_price = 400.0

        gex = compute_option_gex(option, underlying_price)

        # Expected: -(0.006 * 12000 * 100 * 400 * 0.01) = -2,880,000
        expected = -(0.006 * 12000 * 100 * 400 * 0.01)
        assert gex == pytest.approx(expected)
        assert gex < 0  # Puts have negative GEX

    def test_zero_gamma(self):
        """Test with zero gamma."""
        option = {
            'type': 'call',
            'gamma': 0.0,
            'open_interest': 10000,
            'strike': 400
        }
        gex = compute_option_gex(option, 400.0)
        assert gex == 0.0

    def test_zero_open_interest(self):
        """Test with zero open interest."""
        option = {
            'type': 'call',
            'gamma': 0.005,
            'open_interest': 0,
            'strike': 400
        }
        gex = compute_option_gex(option, 400.0)
        assert gex == 0.0

    def test_missing_fields(self):
        """Test with missing fields (should default to 0)."""
        option = {'type': 'call'}
        gex = compute_option_gex(option, 400.0)
        assert gex == 0.0


class TestComputeOptionDEX:
    """Test suite for individual option DEX calculation."""

    def test_call_option_dex(self):
        """Test DEX calculation for a call option."""
        option = {
            'type': 'call',
            'delta': 0.50,
            'open_interest': 10000,
            'strike': 400
        }
        underlying_price = 400.0

        dex = compute_option_dex(option, underlying_price)

        # Expected: 0.50 * 10000 * 100 * 400 = 200,000,000
        expected = 0.50 * 10000 * 100 * 400
        assert dex == pytest.approx(expected)

    def test_put_option_dex(self):
        """Test DEX calculation for a put option."""
        option = {
            'type': 'put',
            'delta': -0.45,
            'open_interest': 12000,
            'strike': 390
        }
        underlying_price = 400.0

        dex = compute_option_dex(option, underlying_price)

        # Expected: -(-0.45 * 12000 * 100 * 400) = 216,000,000
        expected = -(-0.45 * 12000 * 100 * 400)
        assert dex == pytest.approx(expected)


class TestAggregateGEX:
    """Test suite for GEX aggregation."""

    @pytest.fixture
    def sample_options(self):
        """Sample options data for testing."""
        return [
            # Calls
            {'symbol': 'SPY230120C00400000', 'strike': 400, 'type': 'call',
             'gamma': 0.005, 'delta': 0.50, 'open_interest': 10000},
            {'symbol': 'SPY230120C00410000', 'strike': 410, 'type': 'call',
             'gamma': 0.004, 'delta': 0.40, 'open_interest': 8000},
            # Puts
            {'symbol': 'SPY230120P00390000', 'strike': 390, 'type': 'put',
             'gamma': 0.006, 'delta': -0.45, 'open_interest': 12000},
            {'symbol': 'SPY230120P00380000', 'strike': 380, 'type': 'put',
             'gamma': 0.005, 'delta': -0.35, 'open_interest': 9000},
        ]

    def test_aggregate_basic(self, sample_options):
        """Test basic aggregation."""
        underlying_price = 400.0
        result = aggregate_gex(sample_options, underlying_price)

        assert 'total_call_gex' in result
        assert 'total_put_gex' in result
        assert 'net_gex' in result
        assert 'per_strike' in result
        assert 'total_call_oi' in result
        assert 'total_put_oi' in result

        # Check that totals are correct type
        assert isinstance(result['total_call_gex'], float)
        assert isinstance(result['total_put_gex'], float)
        assert isinstance(result['net_gex'], float)

    def test_net_gex_calculation(self, sample_options):
        """Test net GEX calculation."""
        underlying_price = 400.0
        result = aggregate_gex(sample_options, underlying_price)

        # Net GEX should be call GEX minus put GEX
        expected_net = result['total_call_gex'] - result['total_put_gex']
        assert result['net_gex'] == pytest.approx(expected_net)

    def test_per_strike_breakdown(self, sample_options):
        """Test per-strike breakdown."""
        underlying_price = 400.0
        result = aggregate_gex(sample_options, underlying_price)

        per_strike = result['per_strike']

        # Should have 4 strikes
        assert len(per_strike) == 4
        assert 400 in per_strike
        assert 410 in per_strike
        assert 390 in per_strike
        assert 380 in per_strike

        # Check strike 400 (call only)
        assert per_strike[400]['call_gex'] > 0
        assert per_strike[400]['put_gex'] == 0
        assert per_strike[400]['call_oi'] == 10000
        assert per_strike[400]['put_oi'] == 0

        # Check strike 390 (put only)
        assert per_strike[390]['call_gex'] == 0
        assert per_strike[390]['put_gex'] > 0
        assert per_strike[390]['call_oi'] == 0
        assert per_strike[390]['put_oi'] == 12000

    def test_empty_options_list(self):
        """Test with empty options list."""
        result = aggregate_gex([], 400.0)

        assert result['total_call_gex'] == 0.0
        assert result['total_put_gex'] == 0.0
        assert result['net_gex'] == 0.0
        assert len(result['per_strike']) == 0


class TestFindGammaFlipPoint:
    """Test suite for gamma flip point detection."""

    def test_flip_point_found(self):
        """Test finding a flip point."""
        per_strike_net_gex = {
            390: 500000,
            395: 200000,
            400: -100000,
            405: -300000
        }

        flip = find_gamma_flip_point(per_strike_net_gex, 400.0)

        # Should find flip between 395 and 400
        assert flip is not None
        assert 395 < flip < 400

    def test_no_flip_point(self):
        """Test when no flip point exists."""
        per_strike_net_gex = {
            390: 500000,
            395: 700000,
            400: 900000,
            405: 1100000
        }

        flip = find_gamma_flip_point(per_strike_net_gex, 400.0)

        # All positive, no flip
        assert flip is None

    def test_empty_data(self):
        """Test with empty data."""
        flip = find_gamma_flip_point({}, 400.0)
        assert flip is None

    def test_single_strike(self):
        """Test with single strike."""
        flip = find_gamma_flip_point({400: 100000}, 400.0)
        assert flip is None


class TestAnalyzeSymbolGEX:
    """Test suite for complete symbol GEX analysis."""

    @pytest.fixture
    def sample_options(self):
        """Sample options for analysis."""
        return [
            {'symbol': 'SPY230120C00400000', 'strike': 400, 'type': 'call',
             'gamma': 0.005, 'delta': 0.50, 'open_interest': 10000,
             'expiration': '2023-01-20'},
            {'symbol': 'SPY230120P00390000', 'strike': 390, 'type': 'put',
             'gamma': 0.006, 'delta': -0.45, 'open_interest': 12000,
             'expiration': '2023-01-20'},
        ]

    def test_analyze_symbol_gex(self, sample_options):
        """Test complete symbol analysis."""
        result = analyze_symbol_gex(
            symbol='SPY',
            options=sample_options,
            underlying_price=400.0
        )

        # Check result attributes
        assert result.symbol == 'SPY'
        assert result.underlying_price == 400.0
        assert isinstance(result.timestamp, str)
        assert result.total_call_gex > 0
        assert result.total_put_gex > 0
        assert isinstance(result.net_gex, float)
        assert len(result.per_strike) == 2

    def test_timestamp_assignment(self, sample_options):
        """Test timestamp handling."""
        # Without timestamp
        result1 = analyze_symbol_gex('SPY', sample_options, 400.0)
        assert result1.timestamp is not None

        # With timestamp
        custom_time = '2023-01-20T12:00:00'
        result2 = analyze_symbol_gex('SPY', sample_options, 400.0, timestamp=custom_time)
        assert result2.timestamp == custom_time


class TestGEXInterpretation:
    """Test GEX interpretation helper."""

    def test_positive_gex(self):
        """Test positive GEX interpretation."""
        interp = get_gex_interpretation(1000000)
        assert 'Positive' in interp
        assert 'long gamma' in interp or 'Long gamma' in interp

    def test_negative_gex(self):
        """Test negative GEX interpretation."""
        interp = get_gex_interpretation(-1000000)
        assert 'Negative' in interp
        assert 'short gamma' in interp or 'Short gamma' in interp

    def test_zero_gex(self):
        """Test zero GEX interpretation."""
        interp = get_gex_interpretation(0)
        assert 'Neutral' in interp or 'Balanced' in interp


# Integration test
class TestGEXCalculatorIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self):
        """Test complete workflow from options to analysis."""
        # Create sample data
        options = [
            {'strike': 390, 'type': 'call', 'gamma': 0.004, 'delta': 0.30,
             'open_interest': 8000, 'expiration': '2023-01-20'},
            {'strike': 395, 'type': 'call', 'gamma': 0.005, 'delta': 0.45,
             'open_interest': 12000, 'expiration': '2023-01-20'},
            {'strike': 400, 'type': 'call', 'gamma': 0.006, 'delta': 0.55,
             'open_interest': 15000, 'expiration': '2023-01-20'},
            {'strike': 390, 'type': 'put', 'gamma': 0.005, 'delta': -0.35,
             'open_interest': 10000, 'expiration': '2023-01-20'},
            {'strike': 395, 'type': 'put', 'gamma': 0.006, 'delta': -0.45,
             'open_interest': 14000, 'expiration': '2023-01-20'},
            {'strike': 400, 'type': 'put', 'gamma': 0.007, 'delta': -0.50,
             'open_interest': 16000, 'expiration': '2023-01-20'},
        ]

        underlying_price = 397.50

        # Run analysis
        result = analyze_symbol_gex('TEST', options, underlying_price)

        # Verify results
        assert result.symbol == 'TEST'
        assert result.underlying_price == underlying_price
        assert len(result.per_strike) == 3  # 390, 395, 400
        assert result.total_call_oi == 35000
        assert result.total_put_oi == 40000

        # Verify each strike has data
        for strike in [390, 395, 400]:
            assert strike in result.per_strike
            strike_data = result.per_strike[strike]
            assert strike_data.call_gex >= 0
            assert strike_data.put_gex >= 0
            assert strike_data.total_oi > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
