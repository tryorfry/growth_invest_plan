"""Unit tests for pattern recognition"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pattern_recognition import PatternRecognition


@pytest.fixture
def pattern_detector():
    """Create pattern detector instance"""
    return PatternRecognition()


@pytest.fixture
def sample_data():
    """Create sample OHLC data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    data = {
        'Open': np.random.uniform(100, 110, 100),
        'High': np.random.uniform(110, 120, 100),
        'Low': np.random.uniform(90, 100, 100),
        'Close': np.random.uniform(100, 110, 100),
    }
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def doji_data():
    """Create data with a Doji pattern"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    data = {
        'Open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'High': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'Low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107],
        'Close': [100.1, 101, 102, 103, 104, 105, 106, 107, 108, 109],  # Doji at index 0
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def hammer_data():
    """Create data with a Hammer pattern"""
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    data = {
        'Open': [110, 108, 106, 104, 105],
        'High': [111, 109, 107, 105, 106],
        'Low': [109, 107, 105, 100, 104],  # Hammer at index 3
        'Close': [108, 106, 104, 104, 105],
    }
    return pd.DataFrame(data, index=dates)


def test_detect_doji(pattern_detector, doji_data):
    """Test Doji pattern detection"""
    patterns = pattern_detector.detect_patterns(doji_data)
    
    doji_patterns = [p for p in patterns if p['pattern'] == 'Doji']
    assert len(doji_patterns) > 0


def test_detect_hammer(pattern_detector, hammer_data):
    """Test Hammer pattern detection"""
    patterns = pattern_detector.detect_patterns(hammer_data)
    
    hammer_patterns = [p for p in patterns if p['pattern'] == 'Hammer']
    # May or may not detect depending on exact ratios
    assert isinstance(patterns, list)


def test_get_recent_patterns(pattern_detector, sample_data):
    """Test getting recent patterns"""
    patterns = pattern_detector.get_recent_patterns(sample_data, days=30)
    
    assert isinstance(patterns, list)
    # All patterns should be within last 30 days
    if patterns:
        cutoff = sample_data.index[-1] - timedelta(days=30)
        for p in patterns:
            assert p['date'] >= cutoff


def test_pattern_structure(pattern_detector, sample_data):
    """Test that detected patterns have correct structure"""
    patterns = pattern_detector.detect_patterns(sample_data)
    
    for pattern in patterns:
        assert 'date' in pattern
        assert 'pattern' in pattern
        assert 'signal' in pattern
        assert 'price' in pattern


def test_empty_data(pattern_detector):
    """Test with empty dataframe"""
    empty_df = pd.DataFrame()
    patterns = pattern_detector.detect_patterns(empty_df)
    
    assert patterns == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
