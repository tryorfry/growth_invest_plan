"""Factory for instantiating Trading Styles"""
from .base import TradingStyleStrategy
from .growth import GrowthStyle
from .swing import SwingStyle

def get_trading_style(style_name: str) -> TradingStyleStrategy:
    """Factory method to get the requested trading style strategy"""
    if style_name == "Swing Trading":
        return SwingStyle()
        
    # Default to Growth Investing to preserve existing behavior
    return GrowthStyle()
