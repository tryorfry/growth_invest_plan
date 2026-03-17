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

    @abstractmethod
    def score_setup(self, analysis_obj: Any) -> float:
        """
        Returns a score from 0.0 to 1.0 representing the quality of the trade setup.
        1.0 is a perfect setup, 0.0 is no setup or rejected.
        """
        pass

    def _apply_smart_rounding(self, price: float) -> float:
        """Psychological rounding logic for Support/Resistance"""
        if price <= 0:
            return 0.0
            
        max_deviation = 0.02
        
        if price >= 100:
            steps = [100, 50, 20, 10, 5]
        elif price >= 20:
            steps = [10, 5]
        elif price >= 5:
            steps = [5]
        else:
            steps = []
            
        for step in steps:
            nearest_psycho = round(price / step) * step
            if nearest_psycho > 0 and abs(price - nearest_psycho) / price <= max_deviation:
                return float(nearest_psycho)
                
        return float(round(price))

    def get_primary_target(self, analysis: Any) -> float:
        """
        Common logic for determining the primary target price.
        MATP for Stocks, Resistance/ATH for ETFs.
        """
        price = analysis.current_price
        is_etf = any(keyword in str(getattr(analysis, 'industry', '')).lower() for keyword in ['etf', 'exchange traded fund'])
        
        if is_etf:
            # For ETFs, use the next significant resistance or ATH
            all_resistances = sorted([r for r in getattr(analysis, 'resistance_levels', []) if r > price])
            if all_resistances:
                return float(all_resistances[-1])
            else:
                return float(price * 1.10) # Fallback to 10% gain
        else:
            # For Stocks, prioritize Median Analyst Target Price
            target = getattr(analysis, 'median_price_target', None)
            if target:
                return float(target)
            else:
                # Fallback to high resistance for stocks without analyst coverage
                all_resistances = sorted([r for r in getattr(analysis, 'resistance_levels', []) if r > price])
                if all_resistances:
                    return float(all_resistances[-1])
                return float(price * 1.10)

    def calculate_max_buy_price(self, analysis: Any) -> float:
        """
        Standard formula for Maximum Buy Price (Entry Ceiling).
        Formula: Target / 1.15 (providing a 15% upside requirement).
        """
        target = getattr(analysis, 'target_price', None)
        if not target:
            target = self.get_primary_target(analysis)
            
        if target:
            return float(target / 1.15)
        
        # Absolute fallback: 5% above current price if no target found
        return float(analysis.current_price * 1.05)
