"""Unit tests for Trading Formulas (SL = Support - 1 ATR - Noise Buffer)"""

import pytest
import pandas as pd
from unittest.mock import Mock
from src.trading_styles.growth import GrowthStyle
from src.trading_styles.swing import SwingStyle
from src.trading_styles.trend import TrendStyle

class MockAnalysis:
    def __init__(self, current_price, ema20=0, ema50=0, ema200=0, atr=0, atr_daily=0, support_levels=None):
        self.current_price = float(current_price)
        self.ema20 = float(ema20)
        self.ema50 = float(ema50)
        self.ema200 = float(ema200)
        self.atr = float(atr)
        self.atr_daily = float(atr_daily)
        self.support_levels = support_levels or []
        self.resistance_levels = []
        self.volume_profile_hvns = []
        self.suggested_entry = None
        self.suggest_stop_loss = None # Note: typo in base class might be picked up, but analyze uses suggested_stop_loss
        self.suggested_stop_loss = None
        self.target_price = None
        self.reward_to_risk = 0.0
        self.market_trend = "Uptrend"
        self.setup_notes = []
        self.trading_style = ""
        self.history = pd.DataFrame()
        self.atr_used = 0.0
        self.atr_type = ""
        self.last_earnings_date = "2024-01-01"

def test_growth_style_atr_w():
    """Verify Growth Style uses 14w ATR - 10% Noise"""
    # Floor: 100. ATR: 10. Buffer: 1. SL: 100 - 10 - 1 = 89.0.
    # Round down 89.0 -> 88.99
    analysis = MockAnalysis(current_price=105.0, ema50=100.0, ema200=80.0, atr=10.0, atr_daily=5.0, support_levels=[100.0])
    style = GrowthStyle()
    style.calculate_trade_setup(analysis)
    
    assert analysis.suggested_stop_loss == 88.99
    assert analysis.atr_used == 10.0

def test_swing_style_atr_d():
    """Verify Swing Style uses 14d ATR - 10% Noise"""
    # Floor: 100. ATR: 5. Buffer: 0.5. SL: 100 - 5 - 0.5 = 94.5.
    # Round down 94.5 -> 94.44
    analysis = MockAnalysis(current_price=105.0, ema20=100.0, ema50=90.0, atr=10.0, atr_daily=5.0, support_levels=[100.0])
    analysis.resistance_levels = [130.0]
    style = SwingStyle()
    style.calculate_trade_setup(analysis)
    
    assert analysis.suggested_stop_loss == 94.44
    assert analysis.atr_used == 5.0

def test_trend_style_noise_buffer():
    """Verify Trend Style uses 14d ATR - 10% Noise"""
    analysis = MockAnalysis(current_price=110.0, ema20=100.0, ema50=90.0, ema200=80.0, atr=10.0, atr_daily=5.0)
    analysis.history = pd.DataFrame({
        'High': [110]*30, 'Low': [90]*30, 'Close': [105]*30,
        'Trend_Upper': [120]*30, 'Trend_Lower': [80]*30, 'Trend_Center': [100]*30
    })
    style = TrendStyle()
    style.get_primary_target = lambda a: 150.0
    style.calculate_trade_setup(analysis)
    
    # Floor: 100. ATR: 5. Noise: 0.5. SL: 100 - 5 - 0.5 = 94.5.
    # Round down 94.5 -> 94.44
    assert analysis.suggested_stop_loss == 94.44
    assert analysis.atr_used == 5.0

def test_trend_style_extended_price():
    """Verify Trend Style: SL stays near Support even if price is far away (MCD case)"""
    # Current Price: 308.99. Support: 308.99. ATR: 4.97. Noise: 0.497.
    # SL = 308.99 - 4.97 - 0.497 = 303.52 -> 303.44 (rounded)
    analysis = MockAnalysis(current_price=308.99, ema20=308.99, ema50=290.0, ema200=280.0, atr_daily=4.97)
    analysis.history = pd.DataFrame({
        'High': [310]*60, 'Low': [290]*60, 'Close': [300]*60,
        'Trend_Upper': [320]*60, 'Trend_Lower': [280]*60, 'Trend_Center': [300]*60
    })
    
    style = TrendStyle()
    style.get_primary_target = lambda a: 350.0
    style.calculate_trade_setup(analysis)
    
    assert analysis.suggested_stop_loss == 303.44
    assert analysis.atr_used == 4.97
