"""Underlying price source selection in PolygonClient.get_underlying_price."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from polygon_client import PolygonClient


def _client(ticker: dict) -> PolygonClient:
    client = PolygonClient('test-key', min_request_interval=0)
    client._make_request = lambda endpoint, params=None: {'ticker': ticker}
    return client


def test_prefers_last_trade():
    c = _client({'lastTrade': {'p': 770.0}, 'min': {'c': 769.0}, 'day': {'c': 768.0}, 'prevDay': {'c': 760.0}})
    assert c.get_underlying_price('SPY') == 770.0


def test_uses_minute_bar_when_no_last_trade():
    """Starter plans have no lastTrade; the snapshot's minute bar is current."""
    c = _client({'min': {'c': 761.26}, 'day': {'c': 763.25}, 'prevDay': {'c': 771.79}})
    assert c.get_underlying_price('SPY') == 761.26


def test_uses_day_bar_when_no_minute_bar():
    c = _client({'min': {}, 'day': {'c': 763.25}, 'prevDay': {'c': 771.79}})
    assert c.get_underlying_price('SPY') == 763.25


def test_falls_back_to_prev_close_before_the_open():
    c = _client({'min': {'c': 0}, 'day': {'c': 0}, 'prevDay': {'c': 771.79}})
    assert c.get_underlying_price('SPY') == 771.79


def test_no_price_raises():
    with pytest.raises(ValueError):
        _client({}).get_underlying_price('SPY')
