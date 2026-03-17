import math
from typing import Dict, Any, List
from .base import TradingStyleStrategy

class SwingStyle(TradingStyleStrategy):
    """
    Short-term Swing Trading Strategy (1-2 weeks).
    Looks for Momentum trends (EMA20 > EMA50).
    Uses Daily ATR (14d).
    Requires Reward/Risk >= 2.0.
    """
    
    @property
    def style_name(self) -> str:
        return "Swing Trading"
        
    def _apply_smart_rounding(self, price: float) -> float:
        """Original psychological rounding logic"""
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
        Calculates suggested entry, stop loss, and target based on Swing parameters.
        Enforces Risk/Reward >= 2.0.
        """
        price = analysis.current_price
        ema20 = getattr(analysis, 'ema20', 0)
        ema50 = getattr(analysis, 'ema50', 0)
        atr_daily = getattr(analysis, 'atr_daily', getattr(analysis, 'atr', 0)) # Fallback to standard ATR if missing
        notes = []
        
        # 1. Determine Trend (Short-term EMA cross)
        if price > ema20 and ema20 > ema50:
            analysis.market_trend = "Uptrend"
        elif price < ema20 and ema20 < ema50:
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
        
        if not nearest_support or not nearest_resistance or atr_daily <= 0:
            notes.append("❌ Rejected: Insufficient support/resistance data or volatility.")
            analysis.setup_notes = notes
            return

        # 3. Swing Math based on Trend
        if analysis.market_trend == "Uptrend" or analysis.market_trend == "Sideways":
            # Buy near support
            raw_entry = nearest_support * 1.0035 # +0.35%
            entry = self._adjust_decimals(raw_entry, is_entry=True)
            
            raw_stop = nearest_support - atr_daily
            stop_loss = self._adjust_decimals(raw_stop, is_entry=False)
            risk = abs(entry - stop_loss)
            
            # Find a valid target from resistances
            target = None
            reward = 0
            for r in valid_resistances:
                raw_target = r * 0.9965 # -0.35%
                potential_target = self._adjust_decimals(raw_target, is_entry=False)
                potential_reward = abs(potential_target - entry)
                
                if risk > 0 and (potential_reward / risk) >= 2.0:
                    target = potential_target
                    reward = potential_reward
                    if r != valid_resistances[0]:
                        notes.append(f"ℹ️ Extended Target: Using higher resistance to achieve R/R >= 2.0")
                    break
            
            # If no target meets the R/R, default to the nearest resistance so it gets formally rejected
            if target is None and valid_resistances:
                raw_target = nearest_resistance * 0.9965
                target = self._adjust_decimals(raw_target, is_entry=False)
                reward = abs(target - entry)
                
            if analysis.market_trend == "Sideways":
                notes.append("ℹ️ Sideways market: Trading the range (Support to Resistance).")
            
        elif analysis.market_trend == "Downtrend":
            raw_entry = nearest_resistance * 0.9965 # -0.35%
            entry = self._adjust_decimals(raw_entry, is_entry=False) # Selling short
            
            raw_stop = nearest_resistance + atr_daily
            stop_loss = self._adjust_decimals(raw_stop, is_entry=True) # Buy to cover stop
            risk = abs(stop_loss - entry)
            
            # Find a valid target from supports
            target = None
            reward = 0
            # Reverse valid_supports to look downwards from nearest support
            for s in reversed(valid_supports):
                raw_target = s * 1.0035 # +0.35%
                potential_target = self._adjust_decimals(raw_target, is_entry=True) # Buy to cover target
                potential_reward = abs(entry - potential_target)
                
                if risk > 0 and (potential_reward / risk) >= 2.0:
                    target = potential_target
                    reward = potential_reward
                    if s != valid_supports[-1]:
                        notes.append(f"ℹ️ Extended Target: Using lower support to achieve R/R >= 2.0")
                    break
            
            # If no target meets the R/R, default to the nearest support so it gets formally rejected
            if target is None and valid_supports:
                raw_target = nearest_support * 1.0035
                target = self._adjust_decimals(raw_target, is_entry=True)
                reward = abs(entry - target)
            
        else:
            notes.append("❌ Rejected: Unable to determine market trend.")
            analysis.setup_notes = notes
            return
            
        # 4. Enforce Risk/Reward Match
        analysis.suggested_entry = entry
        analysis.suggested_stop_loss = stop_loss
        analysis.target_price = target
        
        # Safe division
        reward_risk_ratio = (reward / risk) if risk > 0 else 0
        analysis.reward_to_risk = reward_risk_ratio
        
        if reward_risk_ratio >= 2.0:
            notes.append(f"✅ Setup Valid: Excellent Reward/Risk ratio ({reward_risk_ratio:.1f}x)")
        else:
            notes.append(f"❌ Rejected: Poor Reward/Risk ratio ({reward_risk_ratio:.1f}x). Must be >= 2.0x.")
            
        analysis.setup_notes = notes
        
        # 5. Pattern Detection for Confirmation
        from src.pattern_recognition import PatternRecognition
        recognizer = PatternRecognition()
        analysis.swing_patterns = recognizer.detect_trend_patterns(
            analysis.history, 
            supports=getattr(analysis, 'support_levels', []), 
            resistances=getattr(analysis, 'resistance_levels', []),
            days=30  # Increased lookback for better pattern visibility
        )
        
    def get_chart_defaults(self) -> Dict[str, Any]:
        """Returns standard UI state preferences for Swing Trading."""
        return {
            'timeframe': 'D',
            'zoom': '1Y',
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
        Scores Swing Trading setup.
        Max 1.0 (100%).
        """
        score = 0.0
        
        # 1. Reward/Risk (40% Weight)
        rr = getattr(analysis, 'reward_to_risk', 0) or 0
        if rr >= 3.0:
            score += 0.4
        elif rr >= 2.0:
            score += 0.25
        elif rr >= 1.5:
            score += 0.1
            
        # 2. Pattern Confirmation (30% Weight)
        patterns = getattr(analysis, 'swing_patterns', [])
        if len(patterns) >= 2:
            score += 0.3
        elif len(patterns) == 1:
            score += 0.15
            
        # 3. Trend Alignment (30% Weight)
        trend = getattr(analysis, 'market_trend', 'Sideways')
        if trend in ["Uptrend", "Downtrend"]:
            score += 0.3
        elif trend == "Sideways":
            score += 0.15
            
        # 4. Rejection Check
        if any("❌ Rejected" in n for n in getattr(analysis, 'setup_notes', [])):
            if score > 0.4: score = 0.4 # Cap score if rejected but technically setup exists
            else: score *= 0.5
            
        return min(1.0, score)
