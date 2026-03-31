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
        industry = str(getattr(analysis, 'industry', '')).lower()
        q_type = str(getattr(analysis, 'quoteType', '')).lower()
        is_etf = 'etf' in industry or 'exchange traded fund' in industry or q_type == 'etf'
        
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
        Formula: Target / (Required Upside).
        Required Upside: 15% for Stocks, 10% for ETFs.
        """
        target = getattr(analysis, 'target_price', None)
        if not target:
            target = self.get_primary_target(analysis)
            
        industry = str(getattr(analysis, 'industry', '')).lower()
        q_type = str(getattr(analysis, 'quoteType', '')).lower()
        is_etf = 'etf' in industry or 'exchange traded fund' in industry or q_type == 'etf'
        
        required_upside = 1.10 if is_etf else 1.15
            
        if target:
            return float(target / required_upside)
        
        # Absolute fallback: 5% above current price if no target found
        return float(analysis.current_price * 1.05)

    def _calculate_rr(self, entry: float, stop: float, target: float, direction: str = "long") -> float:
        """
        Calculates Reward/Risk ratio with directional logic and risk floor.
        Returns 0.0 if the trade is invalid (stop on the wrong side).
        Prevent nonsensical ratios when risk is near-zero.
        """
        if not entry or not stop or not target:
            return 0.0
            
        if direction.lower() == "long":
            risk = entry - stop
            reward = target - entry
        else: # short
            risk = stop - entry
            reward = entry - target
            
        # 1. Directional Check: If stop is on the wrong side or at entry, RR is 0
        if risk <= 0:
            return 0.0
            
        # 2. Risk Floor: Prevent division by near-zero. 
        # Using 0.1% of entry price as a hard minimum risk floor.
        min_risk = entry * 0.001 
        effective_risk = max(risk, min_risk)
        
        return float(reward / effective_risk)
