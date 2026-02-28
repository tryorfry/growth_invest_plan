import pytest
from src.data_sources.options_source import OptionsSource

def test_fetch_options_data():
    """Test standard options chain fetching"""
    source = OptionsSource()
    res = source.fetch_options_data("AAPL")
    
    # Check that we got basic dict
    assert isinstance(res, dict)
    
    # Ignore internet failures
    if res:
        assert 'implied_volatility' in res
        assert 'put_call_ratio' in res
        assert 'total_call_volume' in res

def test_scan_unusual_activity():
    """Test unusual options activity scanner"""
    source = OptionsSource()
    res = source.scan_unusual_activity("AAPL", min_volume=1, vol_oi_ratio=0.1)
    
    assert isinstance(res, list)
    
    # Ignore internet failures
    if res:
        first = res[0]
        assert 'type' in first
        assert 'strike' in first
        assert 'volume' in first
        assert 'open_interest' in first
        assert 'vol_oi_ratio' in first
        assert 'premium_est' in first
        assert 'otm_pct' in first
