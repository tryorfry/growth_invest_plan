import math
from typing import Dict, Any, List
from .base import TradingStyleStrategy

class GrowthStyle(TradingStyleStrategy):
    """
    Original Growth Investing Strategy.
    Looks for Long-term trends (EMA50 > EMA200).
    Entries: Near major Support floors.
    Stops: Below Support - 1 Weekly ATR.
    """
    
    @property
    def style_name(self) -> str:
        return "Growth Investing"
        
        
    def _adjust_decimals(self, price: float, is_entry: bool = True) -> float:
        """Original repeating decimal logic (.11, .22, etc)"""
        valid_cents = [11, 22, 33, 44, 66, 77, 88, 99]
        
        if is_entry:
            int_part = int(math.floor(price))
            cents = round((price - int_part) * 100)
            
            chosen_cent = None
            for v in valid_cents:
                if v >= cents:
                    chosen_cent = v
                    break
            
            if chosen_cent is None:
                int_part += 1
                chosen_cent = 11
                
            return float(int_part) + (chosen_cent / 100.0)
            
        else:
            int_part = int(math.floor(price))
            cents = round((price - int_part) * 100)
            
            chosen_cent = None
            for v in reversed(valid_cents):
                if v <= cents:
                    chosen_cent = v
                    break
                    
            if chosen_cent is None:
                int_part -= 1
                chosen_cent = 99
                
            return float(int_part) + (chosen_cent / 100.0)

    def calculate_trade_setup(self, analysis: Any) -> None:
        """
        Original calculate_trade_setup logic from analyzer.py
        Calculates suggested entry and stop loss based on Growth parameters.
        """
        price = analysis.current_price
        ema50 = analysis.ema50
        ema200 = analysis.ema200
        atr = analysis.atr  # Weekly ATR
        notes = []
        
        # 1. Determine Trend (Long-term EMA cross)
        if price > ema50 and ema50 > ema200:
            analysis.market_trend = "Uptrend"
        elif price < ema50 and ema50 < ema200:
            analysis.market_trend = "Downtrend"
        else:
            analysis.market_trend = "Sideways"
            
        # 2. Compile Support and Resistance
        all_supports = sorted(getattr(analysis, 'support_levels', []) + getattr(analysis, 'volume_profile_hvns', []))
        all_resistances = sorted(getattr(analysis, 'resistance_levels', []) + getattr(analysis, 'volume_profile_hvns', []))
        
        valid_supports = [s for s in all_supports if s < price]
        valid_resistances = [r for r in all_resistances if r > price]
        
        nearest_support = valid_supports[-1] if valid_supports else None
        nearest_resistance = valid_resistances[0] if valid_resistances else None
        
        # 3. Check for structural overextension
        if valid_supports and getattr(analysis, 'volume_profile_hvns', []):
            highest_hvn_support = max([h for h in analysis.volume_profile_hvns if h < price], default=None)
            if highest_hvn_support and (price - highest_hvn_support) / highest_hvn_support > 0.20:
                notes.append(f"⚠️ Warning: Price is >20% overextended from highest HVN base (${highest_hvn_support:.2f}).")
        
        if not nearest_support or atr <= 0:
            notes.append("❌ Rejected: Insufficient support data or volatility.")
            analysis.setup_notes = notes
            return
            
        # Execute Entry math
        raw_entry = nearest_support * 1.005 # 0.5% buffer above nearest floor
        entry = self._adjust_decimals(raw_entry, is_entry=True)
        
        # Execute Stop Loss math
        stop_loss_raw = nearest_support - atr
        stop_loss = self._adjust_decimals(stop_loss_raw, is_entry=False)
        
        analysis.suggested_entry = entry
        analysis.suggested_stop_loss = stop_loss
        
        # Calculate target and R/R ratio
        target = self.get_primary_target(analysis)
        analysis.target_price = target
        
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        analysis.reward_to_risk = (reward / risk) if risk > 0 else 0.0
        
        # Maximum buy ceiling
        analysis.max_buy_price = self.calculate_max_buy_price(analysis)
        # 4. Ceiling Check
        if nearest_resistance:
            if (nearest_resistance - price) / price < 0.015:
                notes.append(f"❌ Rejected: Current price is squeezed against resistance ceiling (${nearest_resistance:.2f}). Waiting for Breakout.")
            else:
                notes.append(f"✅ Setup Valid: Clear room before next resistance target (${nearest_resistance:.2f})")
        else:
            notes.append("✅ Setup Valid: Blue Sky (No immediate resistance ceilings detected).")
            
        analysis.setup_notes = notes
        
    def get_chart_defaults(self) -> Dict[str, Any]:
        """Returns standard UI state preferences for Growth Investing."""
        return {
            'timeframe': 'W',
            'zoom': '5Y',
            'ema': True,
            'atr': True,
            'sr': True,
            'ts': True,
            'rsi': False,
            'macd': False,
            'boll': False
        }

    def score_setup(self, analysis: Any) -> float:
        """
        Scores Growth Investing setup.
        Max 1.0 (100%).
        """
        score = 0.0
        
        # 1. Trend (40% Weight)
        if analysis.market_trend == "Uptrend":
            score += 0.4
        elif analysis.market_trend == "Sideways":
            score += 0.1
            
        # 2. Support Proximity (30% Weight)
        # Check if price is within 2 ATRs of the suggested entry (which is near support)
        if getattr(analysis, 'suggested_entry', None) and analysis.atr > 0:
            dist = abs(analysis.current_price - analysis.suggested_entry) / analysis.atr
            if dist <= 1.0: # Excellent proximity
                score += 0.3
            elif dist <= 2.0: # Moderate proximity
                score += 0.15
        
        # 3. Rejection Check (Deduction)
        if any("❌ Rejected" in n for n in getattr(analysis, 'setup_notes', [])):
            return 0.0 # Strict rejection for Growth
            
        # 4. Fundamental Quality (30% Weight - simplified checklist)
        # Using ROE and EPS growth as proxies
        from src.utils import _safe_float_parse
        roe = _safe_float_parse(analysis.finviz_data.get('ROE', ''))
        eps_ny = _safe_float_parse(analysis.finviz_data.get('EPS next Y', ''))
        
        if roe and roe >= 15: score += 0.15
        if eps_ny and eps_ny >= 15: score += 0.15
        
        return min(1.0, score)
