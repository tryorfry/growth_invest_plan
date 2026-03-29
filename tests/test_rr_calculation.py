import pytest
from src.trading_styles.trend import TrendStyle
from src.trading_styles.swing import SwingStyle
from src.trading_styles.growth import GrowthStyle
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class MockAnalysis:
    current_price: float = 100.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0
    atr: float = 0.0
    atr_daily: float = 0.0
    history: Any = None
    industry: str = "Technology"
    median_price_target: float = 120.0
    resistance_levels: List[float] = field(default_factory=list)
    support_levels: List[float] = field(default_factory=list)
    market_trend: str = ""
    suggested_entry: float = 0.0
    suggested_stop_loss: float = 0.0
    target_price: float = 0.0
    reward_to_risk: float = 0.0
    setup_notes: List[str] = field(default_factory=list)
    volume_profile_hvns: List[float] = field(default_factory=list)

def test_rr_directional_long_invalid():
    """Test that a long trade with stop above entry returns 0 R/R"""
    style = TrendStyle()
    # entry 100, stop 101, target 120 -> Risk -1 -> RR 0
    rr = style._calculate_rr(entry=100.0, stop=101.0, target=120.0, direction="long")
    assert rr == 0.0

def test_rr_directional_short_invalid():
    """Test that a short trade with stop below entry returns 0 R/R"""
    style = SwingStyle()
    # entry 100, stop 99, target 80 -> Risk -1 -> RR 0
    rr = style._calculate_rr(entry=100.0, stop=99.0, target=80.0, direction="short")
    assert rr == 0.0

def test_rr_risk_floor():
    """Test that a very tight stop is capped by the risk floor (0.1% of entry)"""
    style = TrendStyle()
    entry = 100.0
    target = 110.0
    # True Risk = 100 - 99.999 = 0.001
    # Risk Floor = 100 * 0.001 = 0.1
    # Expected RR = (110 - 100) / 0.1 = 100.0
    rr = style._calculate_rr(entry=entry, stop=99.999, target=target, direction="long")
    assert rr == 100.0
    
    # Without floor, it would be 10 / 0.001 = 10000.0
    assert rr < 1000.0 

def test_trend_style_fix_verification():
    """Verifies TrendStyle uses the new RR logic in its calculate_trade_setup"""
    style = TrendStyle()
    # Mock the AAPL scenario: Sideways/Downtrend, Entry 251.64, Stop 251.65, Target 280
    analysis = MockAnalysis(
        current_price=251.64,
        ema20=252.0, # Will result in SL around 251.64 + buffer
        atr=0.45,
        median_price_target=280.0
    )
    # Force Sideways/Downtrend path
    style.calculate_trade_setup(analysis)
    
    # If Stop was 251.65 and Entry 251.64, RR should be 0.0
    if analysis.suggested_stop_loss >= analysis.suggested_entry:
        assert analysis.reward_to_risk == 0.0
    else:
        # If it's valid, it should still have the floor applied if risk is tiny
        risk = analysis.suggested_entry - analysis.suggested_stop_loss
        if risk < analysis.suggested_entry * 0.001:
            expected = (analysis.target_price - analysis.suggested_entry) / (analysis.suggested_entry * 0.001)
            assert pytest.approx(analysis.reward_to_risk) == expected
