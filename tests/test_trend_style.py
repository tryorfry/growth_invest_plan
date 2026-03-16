import pytest
import pandas as pd
import numpy as np
from src.trading_styles.trend import TrendStyle
from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class MockAnalysis:
    current_price: float = 100.0
    ema20: float = 110.0
    ema50: float = 105.0
    ema200: float = 90.0
    atr: float = 5.0
    history: pd.DataFrame = field(default_factory=pd.DataFrame)
    industry: str = "Technology"
    median_price_target: float = 150.0
    resistance_levels: List[float] = field(default_factory=list)
    market_trend: str = ""
    suggested_entry: float = 0.0
    suggested_stop_loss: float = 0.0
    target_price: float = 0.0
    reward_to_risk: float = 0.0
    setup_notes: List[str] = field(default_factory=list)

def test_trend_style_ema_success():
    style = TrendStyle()
    # Setup for successful EMA crossover: 20 > 50 > 200, price > 50
    analysis = MockAnalysis(
        current_price=110.0, # Lower entry
        ema20=110.0,
        ema50=105.0,
        ema200=90.0,
        atr=5.0,
        median_price_target=150.0 # Reward = 40, Risk = 110 - (105-5) = 10. R/R = 4.0
    )
    
    style.calculate_trade_setup(analysis)
    
    assert "Uptrend (EMA)" in analysis.market_trend
    assert analysis.reward_to_risk >= 3.0
    assert analysis.suggested_stop_loss == 105.0 - 5.0 # ema50 - atr
    assert any("EMA Cross" in note for note in analysis.setup_notes)

def test_trend_style_low_rr():
    style = TrendStyle()
    # High risk, low reward
    analysis = MockAnalysis(
        current_price=140.0,
        ema20=110.0,
        ema50=105.0,
        ema200=90.0,
        atr=20.0, # High SL
        median_price_target=150.0 # Low reward
    )
    
    style.calculate_trade_setup(analysis)
    
    assert any("Rejected" in note for note in analysis.setup_notes)
    assert analysis.reward_to_risk < 3.0

def test_trend_style_etf_target():
    style = TrendStyle()
    analysis = MockAnalysis(
        current_price=100.0,
        industry="Exchange Traded Fund",
        resistance_levels=[120.0, 140.0],
        ema20=95.0, ema50=90.0, ema200=80.0, atr=5.0
    )
    
    style.calculate_trade_setup(analysis)
    
    assert analysis.target_price == 140.0
    assert "ETF Target" in "".join(analysis.setup_notes)
    
def test_trend_style_chart_defaults():
    style = TrendStyle()
    defaults = style.get_chart_defaults()
    assert defaults['timeframe'] == 'D'
    assert defaults['zoom'] == '1Y'
