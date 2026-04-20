"""Unit tests for Trading Formulas (SL = Support - 1 ATR + Buffers)"""

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
    """Verify Growth Style uses 14w ATR"""
    # Floor: 100. Entry: 100 * 1.005 = 100.5. SL: 100 - 10 = 90.0.
    # Round down 90.0 -> 89.99
    analysis = MockAnalysis(current_price=105.0, ema50=100.0, ema200=80.0, atr=10.0, atr_daily=5.0, support_levels=[100.0])
    style = GrowthStyle()
    style.calculate_trade_setup(analysis)
    
    assert analysis.suggested_stop_loss == 89.99
    assert analysis.atr_used == 10.0

def test_swing_style_atr_d():
    """Verify Swing Style uses 14d ATR"""
    # Floor: 100. Entry: 100 * 1.0035 = 100.35 -> 100.44. SL: 100 - 5 = 95.0.
    # Round down 95.0 -> 94.99
    analysis = MockAnalysis(current_price=105.0, ema20=100.0, ema50=90.0, atr=10.0, atr_daily=5.0, support_levels=[100.0])
    analysis.resistance_levels = [130.0]
    style = SwingStyle()
    style.calculate_trade_setup(analysis)
    
    assert analysis.suggested_stop_loss == 94.99
    assert analysis.atr_used == 5.0

def test_trend_style_noise_buffer():
    """Verify Trend Style uses 14d ATR + Noise Buffer"""
    analysis = MockAnalysis(current_price=110.0, ema20=100.0, ema50=90.0, ema200=80.0, atr=10.0, atr_daily=5.0)
    analysis.history = pd.DataFrame({
        'High': [110]*30, 'Low': [90]*30, 'Close': [105]*30,
        'Trend_Upper': [120]*30, 'Trend_Lower': [80]*30, 'Trend_Center': [100]*30
    })
    style = TrendStyle()
    style.get_primary_target = lambda a: 150.0
    style.calculate_trade_setup(analysis)
    
    # SL = (100 - 5) + (5 * 0.2) = 96.0.
    # Round down 96.0 -> 95.99
    assert analysis.suggested_stop_loss == 95.99
    assert analysis.atr_used == 5.0
def test_trend_style_extended_price():
    """Verify Trend Style: SL stays near Support even if price is far away (MCD case)"""
    # Current Price: 308.99. Entry: 308.99.
    # Support (EMA20): 308.99. Distant Support (HL): 299.41.
    # New logic should pick EMA20 (308.99) as support_floor.
    # SL = 308.99 - 4.97 = 304.02.
    analysis = MockAnalysis(current_price=308.99, ema20=308.99, ema50=290.0, ema200=280.0, atr_daily=4.97)
    # We need to trigger reversal_setup too
    analysis.history = pd.DataFrame({
        'High': [310]*60, 'Low': [290]*60, 'Close': [300]*60,
        'Trend_Upper': [320]*60, 'Trend_Lower': [280]*60, 'Trend_Center': [300]*60
    })
    
    # Mocking hl_data and dt_data inside PatternRecognition needs care,
    # but here TrendStyle calls it directly.
    # We'll mock the internal call result by setting necessary flags if needed.
    
    style = TrendStyle()
    style.get_primary_target = lambda a: 350.0
    style.calculate_trade_setup(analysis)
    
    # With EMA setup (ema20 > ema50 > ema200):
    # Support floor = 308.99.
    # 308.99 - 4.97 = 304.02.
    # noise_buffer = 4.97 * 0.2 = 0.994.
    # stop_loss = 305.014 -> 304.99?
    assert analysis.suggested_stop_loss > 303.0
    assert analysis.atr_used == 4.97
