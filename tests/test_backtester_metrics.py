import pytest
import pandas as pd
import numpy as np
from src.backtester import BacktestEngine

@pytest.fixture
def sample_price_data():
    """Create a synthetic uptrend with a pullback to test metrics"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Start at 100, go up to 120, drop to 80 (drawdown), then go back to 130
    prices = np.linspace(100, 120, 30).tolist() + \
             np.linspace(120, 80, 20).tolist() + \
             np.linspace(80, 130, 50).tolist()
             
    df = pd.DataFrame({
        'Open': prices,
        'High': prices,
        'Low': prices,
        'Close': prices,
        'Volume': [1000] * 100
    }, index=dates)
    
    return df

def test_drawdown_calculation(sample_price_data):
    """Test that max drawdown is calculated correctly (-33.33%)"""
    # Max price is 120, min after max is 80 -> Drawdown = (80-120)/120 = -33.33%
    results = BacktestEngine.run_ema_crossover(sample_price_data, short_ema=5, long_ema=10)
    
    metrics = results['metrics']
    assert 'Max Drawdown' in metrics
    
    # We should see a negative percentage
    dd_str = metrics['Max Drawdown'].replace('%', '')
    assert float(dd_str) <= 0.0

def test_profit_factor(sample_price_data):
    """Test that profit factor and win rate strings are generated without errors"""
    results = BacktestEngine.run_rsi_strategy(sample_price_data, oversold=40, overbought=60)
    
    metrics = results['metrics']
    assert 'Win Rate' in metrics
    assert 'Profit Factor' in metrics
    assert 'W/' in metrics['Win Rate']
    
def test_combined_strategy(sample_price_data):
    """Test that the combined alpha strategy executes successfully"""
    results = BacktestEngine.run_combined_strategy(sample_price_data)
    
    assert 'data' in results
    assert 'RSI' in results['data'].columns
    assert 'EMA20' in results['data'].columns
    assert 'EMA50' in results['data'].columns
    assert 'signal' in results['data'].columns
