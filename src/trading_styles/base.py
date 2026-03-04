"""Base class for all trading style strategies"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class TradingStyleStrategy(ABC):
    """
    Abstract Strategy pattern defining behavior specific to 
    various trading styles (Growth, Swing, Intraday, etc.)
    """
    
    @property
    @abstractmethod
    def style_name(self) -> str:
        """Name of the strategy for tracking and UI display"""
        pass
        
    @abstractmethod
    def calculate_trade_setup(self, analysis_obj: Any) -> None:
        """
        Calculates the specific entry, target, stop loss, and trend
        for the given trading style. Modifies analysis_obj in-place.
        """
        pass
        
    @abstractmethod
    def get_chart_defaults(self) -> Dict[str, Any]:
        """
        Returns the default UI/chart rendering settings for this style
        (e.g., zoom range, which indicators to turn on/off).
        """
        pass
