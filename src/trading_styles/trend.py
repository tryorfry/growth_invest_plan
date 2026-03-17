import math
from typing import Dict, Any, List
from .base import TradingStyleStrategy

class TrendStyle(TradingStyleStrategy):
    """
    Mid-term Trend Trading Strategy (Months).
    Strategy 1: EMA Cross (20 > 50 > 200).
    Strategy 2: Relative High/Low Reversal (Break Downtrend, HH/HL).
    Requires Reward/Risk >= 3.0.
    """
    
    @property
    def style_name(self) -> str:
        return "Trend Trading"
        
    def _adjust_decimals(self, price: float, is_entry: bool = True) -> float:
        """Standard decimal adjustment for consistency"""
        # Using a simplified version of the swing rounding for trend
        if is_entry:
            return round(price, 2)
        else:
            return round(price, 2)

    def calculate_trade_setup(self, analysis: Any) -> None:
        """
        Calculates suggested entry, stop loss, and target based on Trend parameters.
        Enforces Risk/Reward >= 3.0.
        """
        price = analysis.current_price
        ema20 = getattr(analysis, 'ema20', 0)
        ema50 = getattr(analysis, 'ema50', 0)
        ema200 = getattr(analysis, 'ema200', 0)
        # Use 14-day ATR for Trend Trading as requested
        atr = getattr(analysis, 'atr_daily', getattr(analysis, 'atr', 0)) 
        notes = []
        
        target = self.get_primary_target(analysis)
        if getattr(analysis, 'median_price_target', None) == target:
            notes.append(f"ℹ️ Stock Target: Using Analyst Target Price ${target:.2f}")
        else:
            notes.append(f"ℹ️ Asset Target: Using technical level ${target:.2f}")

        if not target or atr <= 0:
            notes.append("❌ Rejected: Missing target price or ATR data.")
            analysis.setup_notes = notes
            return

        # 1. EMA Strategy Identification
        ema_setup = price > ema50 and ema20 > ema50 and ema50 > ema200
        
        # 2. Relative High/Low Strategy Identification
        from src.pattern_recognition import PatternRecognition
        recognizer = PatternRecognition()
        hl_data = recognizer.detect_relative_high_low(analysis.history)
        dt_data = recognizer.detect_downtrend_line_break(analysis.history)
        
        reversal_setup = dt_data.get('setup', False) and hl_data.get('trend') == "Uptrend"

        # Determine Entry & Stop Loss
        entry = price
        stop_loss = 0
        
        methods_found = []
        if ema_setup: methods_found.append("EMA Cross")
        if reversal_setup: methods_found.append("Relative High/Low")

        if reversal_setup:
            analysis.market_trend = "Uptrend (Reversal)"
            # SL below recent support HL - 1x ATR
            pivots = hl_data.get('pivots', [])
            last_hl = next((p['price'] for p in reversed(pivots) if p['type'] == 'HL'), price * 0.95)
            stop_loss = last_hl - atr
            description = "Relative High/Low Reversal"
            if ema_setup:
                description += " + EMA Confirmation"
            notes.append(f"✅ Strategy: {description}")
        elif ema_setup:
            analysis.market_trend = "Uptrend (EMA)"
            # SL below rebound EMA - 1x ATR
            support_ema = min(ema20, ema50)
            stop_loss = support_ema - atr
            notes.append("✅ Strategy: EMA Trend Reversal (20 > 50 > 200)")
        else:
            analysis.market_trend = "Sideways/Downtrend"
            # Default to EMA 50 support for SL if neither flags
            stop_loss = ema50 - atr if ema50 > 0 else price * 0.90
            notes.append("⚠️ No clear Trend setup detected (Wait for HL/HH or EMA cross).")

        if methods_found:
            notes.append(f"ℹ️ Detection Method(s): {', '.join(methods_found)}")
            if reversal_setup and not ema_setup:
                notes.append("⚡ Note: Relative High/Low detected reversal faster than EMA.")

        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        reward_risk_ratio = (reward / risk) if risk > 0 else 0

        analysis.suggested_entry = entry
        analysis.suggested_stop_loss = stop_loss
        analysis.target_price = target
        analysis.reward_to_risk = reward_risk_ratio
        
        # Calculate Max Buy Price for Trend Trading
        analysis.max_buy_price = self.calculate_max_buy_price(analysis)
        
        if reward_risk_ratio >= 3.0:
            notes.append(f"✅ Setup Valid: Excellent Reward/Risk ratio ({reward_risk_ratio:.1f}x)")
        else:
            notes.append(f"❌ Rejected: Reward/Risk ratio ({reward_risk_ratio:.1f}x) is below 3.0.")

        analysis.setup_notes = notes

    def get_chart_defaults(self) -> Dict[str, Any]:
        """Returns standard UI state preferences for Trend Trading."""
        return {
            'timeframe': 'D', # Daily timeframe as requested
            'zoom': '1Y',    # 1 Year zoom as requested
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
        Scores Trend Trading setup.
        Max 1.0 (100%).
        """
        score = 0.0
        
        # 1. Reward/Risk (40% Weight)
        rr = getattr(analysis, 'reward_to_risk', 0) or 0
        if rr >= 5.0:
            score += 0.4
        elif rr >= 3.0:
            score += 0.25
        elif rr >= 2.0:
            score += 0.1
            
        # 2. Strategy Alignment (40% Weight)
        notes = getattr(analysis, 'setup_notes', [])
        has_ema = any("EMA Trend" in n for n in notes)
        has_reversal = any("Relative High/Low" in n for n in notes)
        
        if has_ema and has_reversal:
            score += 0.4
        elif has_ema or has_reversal:
            score += 0.25
            
        # 3. Trend Quality (20% Weight)
        trend = getattr(analysis, 'market_trend', 'Sideways')
        if "Uptrend" in trend:
            score += 0.2
        elif "Sideways" in trend:
            score += 0.05
            
        # 4. Rejection Check
        if any("❌ Rejected" in n for n in notes):
            if score > 0.4: score = 0.4
            else: score *= 0.5
            
        return min(1.0, score)
