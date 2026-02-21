"""Unit tests for the Mathematical Models module"""

import pytest
import pandas as pd
import numpy as np
import datetime
from src.math_models import MonteCarloEngine

@pytest.fixture
def sample_history():
    """Create a sample stock price history dataframe"""
    dates = pd.date_range(start="2024-01-01", periods=100, freq='B')
    
    # Synthesize somewhat realistic lognormal prices
    np.random.seed(42)  # For deterministic tests
    returns = np.random.normal(loc=0.0005, scale=0.015, size=100) # Bullish drift, 1.5% daily volatility
    prices = 100 * np.exp(np.cumsum(returns))
    
    return pd.DataFrame({'Close': prices}, index=dates)

def test_monte_carlo_gbm(sample_history):
    engine = MonteCarloEngine()
    
    # Test 30 day simulation with 100 paths
    # (Reduced simulations for speed in testing)
    current_price = sample_history['Close'].iloc[-1]
    results = engine.simulate_gbm(current_price, sample_history, days_out=30, num_simulations=100)
    
    # Validate result dictionary structure
    assert "paths" in results
    assert "final_prices" in results
    assert "percentiles" in results
    assert "expected_value" in results
    assert "prob_higher" in results
    assert "metrics" in results
    
    # Validate math logical bounds
    paths = results["paths"]
    assert paths.shape == (31, 100)  # 31 days (including day 0), 100 paths
    
    percentiles = results["percentiles"]
    assert percentiles["p5"] <= percentiles["p50"]
    assert percentiles["p50"] <= percentiles["p95"]
    assert 0 <= results["prob_higher"] <= 100
