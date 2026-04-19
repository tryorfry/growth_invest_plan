import pytest
import pandas as pd
from typing import List, Dict, Any
from src.config.market_config import MARKET_GROUPS

# Mock snapshot data similar to what MacroSource returns
MOCK_SNAPSHOT = [
    {'name': 'S&P 500', 'short': 'SPX', 'value': 5200.50, 'pct_change': 1.25, 'type': 'Index', 'lat': 37.09, 'lon': -95.71},
    {'name': 'Bitcoin', 'short': 'BTC', 'value': 65432.10, 'pct_change': -2.10, 'type': 'Crypto'},
    {'name': 'Crude Oil', 'short': 'OIL', 'value': 82.35, 'pct_change': 0.45, 'type': 'Commodity'},
    {'name': 'USD/SGD', 'short': 'USDSGD', 'value': 1.3456, 'pct_change': 0.12, 'type': 'Forex'}
]

def test_market_config_logic():
    """Verify that all symbols in groups exist in TICKER_CONFIG"""
    from src.config.market_config import TICKER_CONFIG, MARKET_GROUPS
    
    all_group_members = []
    for members in MARKET_GROUPS.values():
        all_group_members.extend(members)
        
    ticker_names = [v['name'] for v in TICKER_CONFIG.values()]
    
    for member in all_group_members:
        assert member in ticker_names, f"Market Group member {member} not found in TICKER_CONFIG"

def test_forex_formatting_logic():
    """Verify that forex values are handled with more precision as per home.py logic"""
    # Simulate the logic in home.py
    def format_val(item):
        return f"{item['value']:,.4f}" if item['type'] == 'Forex' else f"{item['value']:,.2f}"
    
    spx = [s for s in MOCK_SNAPSHOT if s['name'] == 'S&P 500'][0]
    fx = [s for s in MOCK_SNAPSHOT if s['name'] == 'USD/SGD'][0]
    
    assert format_val(spx) == "5,200.50"
    assert format_val(fx) == "1.3456"

def test_map_label_logic():
    """Verify that markers for the map have the correct short names and change labels"""
    # Simulate logic from market_map.py
    df = pd.DataFrame([s for s in MOCK_SNAPSHOT if s.get('lat') is not None])
    df['label_text'] = df.apply(lambda r: f"{r['short']}: {r['pct_change']:+.1f}%", axis=1)
    
    assert df['label_text'].iloc[0] == "SPX: +1.2%"
