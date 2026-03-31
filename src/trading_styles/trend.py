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
        """Strict psychological repeating decimal logic (.11, .22, etc)"""
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
        Calculates suggested entry, stop loss, and target based on Trend parameters.
        Enforces Risk/Reward >= 3.0.
        """
        price = analysis.current_price
        ema20 = getattr(analysis, 'ema20', 0)
        ema50 = getattr(analysis, 'ema50', 0)
        ema200 = getattr(analysis, 'ema200', 0)
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

        # ── Channel data ──────────────────────────────────────────────────────
        hist = getattr(analysis, 'history', None)
        channel_direction = getattr(analysis, 'channel_direction', 'Flat')
        channel_top = float(hist['Trend_Upper'].iloc[-1]) if hist is not None and 'Trend_Upper' in hist.columns and not hist['Trend_Upper'].isna().iloc[-1] else None
        channel_bot = float(hist['Trend_Lower'].iloc[-1]) if hist is not None and 'Trend_Lower' in hist.columns and not hist['Trend_Lower'].isna().iloc[-1] else None
        channel_mid = float(hist['Trend_Center'].iloc[-1]) if hist is not None and 'Trend_Center' in hist.columns and not hist['Trend_Center'].isna().iloc[-1] else None

        # ── Improvement #2: Channel slope classification ──────────────────────
        direction_emoji = {"Rising": "📈", "Flat": "➡️", "Falling": "📉"}.get(channel_direction, "➡️")
        notes.append(f"{direction_emoji} Channel Direction: {channel_direction}")

        # ── Improvement #3: Channel breakout / bounce detection ───────────────
        channel_signal = None
        if channel_top is not None and price > channel_top:
            notes.append("🚀 Breakout: Price has broken above the Channel Top — momentum buy signal!")
            channel_signal = "breakout_up"
        elif channel_bot is not None and price < channel_mid and abs(price - channel_bot) / price < 0.015:
            notes.append("🎯 Channel Bounce: Price near Channel Bottom — potential support buy.")
            channel_signal = "bounce_bot"

        # ── Strategy Identification ───────────────────────────────────────────
        ema_setup = price > ema50 and ema20 > ema50 and ema50 > ema200

        from src.pattern_recognition import PatternRecognition
        recognizer = PatternRecognition()
        hl_data = recognizer.detect_relative_high_low(analysis.history)
        dt_data = recognizer.detect_downtrend_line_break(analysis.history)
        reversal_setup = dt_data.get('setup', False) and hl_data.get('trend') == "Uptrend"

        # ── Improvement #8: Multi-timeframe weekly EMA confirmation ───────────
        weekly_ema20 = getattr(analysis, 'weekly_ema20', None)
        weekly_ema50 = getattr(analysis, 'weekly_ema50', None)
        weekly_trend_confirmed = False
        if weekly_ema20 is not None and weekly_ema50 is not None:
            weekly_trend_confirmed = weekly_ema20 > weekly_ema50
            if weekly_trend_confirmed:
                notes.append("✅ Weekly Confirmed: Weekly EMA20 > EMA50 (multi-timeframe bullish).")
            else:
                notes.append("⚠️ Weekly Caution: Weekly EMA20 ≤ EMA50 — trend not confirmed on weekly view.")

        # ── Determine Entry & Stop Loss ───────────────────────────────────────
        entry = 0
        stop_loss = 0
        strategy_reason = ""

        methods_found = []
        if ema_setup: methods_found.append("EMA Cross")
        if reversal_setup: methods_found.append("Relative High/Low")

        if reversal_setup:
            analysis.market_trend = "Uptrend (Reversal)"
            pivots = hl_data.get('pivots', [])
            last_hl = next((p['price'] for p in reversed(pivots) if p['type'] == 'HL'), price * 0.95)
            # Entry: Near the recent breakout or slight pullback to HL
            # If price is far above HL, wait for EMA20
            target_entry = max(last_hl, ema20) if ema20 > 0 else last_hl
            entry = self._adjust_decimals(target_entry, is_entry=True)
            
            # SL = support_level - 1xATR + noise buffer
            sl_base = target_entry - atr
            noise_buffer = atr * 0.2
            stop_loss = sl_base + noise_buffer
            
            strategy_reason = "Relative High/Low Reversal"
            if ema_setup:
                strategy_reason += " + EMA Confirmation"
            notes.append(f"✅ Strategy: {strategy_reason}. Entry set near support cluster (${entry:.2f}).")
            
        elif ema_setup:
            analysis.market_trend = "Uptrend (EMA)"
            # Entry: Pullback to EMA20 is ideal for Trend Trading
            entry = self._adjust_decimals(ema20, is_entry=True)
            
            # SL = EMA20 - 1×ATR + noise buffer
            sl_base = ema20 - atr
            noise_buffer = atr * 0.2
            stop_loss = sl_base + noise_buffer
            notes.append(f"✅ Strategy: EMA Trend Following (EMA20 > EMA50 > EMA200). Entry suggested at EMA20 (${entry:.2f}). SL below ATR buffer.")
        else:
            analysis.market_trend = "Sideways/Downtrend"
            # No clear entry for Trend Trading in Downtrend
            entry = self._adjust_decimals(price, is_entry=True) # Fallback
            
            sl_base = min(ema20 - atr, price * 0.95) if ema20 > 0 else price * 0.90
            noise_buffer = atr * 0.2
            stop_loss = sl_base + noise_buffer
            
            if stop_loss >= entry:
                stop_loss = entry * 0.94
                
            notes.append("⚠️ No clear Trend setup detected (Wait for HL/HH or EMA cross).")
        if methods_found:
            notes.append(f"ℹ️ Detection Method(s): {', '.join(methods_found)}")
            if reversal_setup and not ema_setup:
                notes.append("⚡ Note: Relative High/Low detected reversal faster than EMA.")


        # ── Improvement #9: Channel Bot + HVN convergence ─────────────────────
        hvns = getattr(analysis, 'volume_profile_hvns', [])
        if channel_bot is not None and hvns:
            close_hvn = min(hvns, key=lambda h: abs(h - channel_bot))
            if abs(close_hvn - channel_bot) / channel_bot < 0.015:  # within 1.5%
                notes.append(f"💎 Strong Support: Channel Bottom (${channel_bot:.2f}) aligns with HVN (${close_hvn:.2f}) — high-confluence support zone!")

        # ── Improvement #10: Earnings proximity risk warning ──────────────────
        days_until = getattr(analysis, 'days_until_earnings', None)
        if days_until is not None and 0 <= days_until <= 10:
            next_e = getattr(analysis, 'next_earnings_date', None)
            date_str = f" ({next_e.strftime('%m/%d')})" if next_e else ""
            notes.append(f"⚠️ Earnings Risk: Earnings in {days_until} day(s){date_str}! Price may gap significantly. Consider waiting until after earnings before entering.")

        reward_risk_ratio = self._calculate_rr(entry, stop_loss, target)

        analysis.suggested_entry = entry
        analysis.suggested_stop_loss = stop_loss
        analysis.target_price = target
        analysis.reward_to_risk = reward_risk_ratio
        analysis.max_buy_price = self.calculate_max_buy_price(analysis)

        if reward_risk_ratio >= 3.0:
            notes.append(f"✅ Setup Valid: Excellent Reward/Risk ratio ({reward_risk_ratio:.1f}x)")
        else:
            notes.append(f"❌ Rejected: Reward/Risk ratio ({reward_risk_ratio:.1f}x) is below 3.0.")

        analysis.setup_notes = notes

    def get_chart_defaults(self) -> Dict[str, Any]:
        """Returns standard UI state preferences for Trend Trading."""
        return {
            'timeframe': 'D',
            'zoom': '1Y',
            'ema': True,
            'atr': True,
            'sr': True,
            'ts': True,
            'rsi': False,
            'macd': False,
            'boll': False,
            'channel': True,
        }

    def score_setup(self, analysis: Any) -> float:
        """
        Scores Trend Trading setup.
        Max 1.0 (100%).
        """
        score = 0.0

        # 1. Reward/Risk (30% Weight)
        rr = getattr(analysis, 'reward_to_risk', 0) or 0
        if rr >= 5.0:
            score += 0.30
        elif rr >= 3.0:
            score += 0.20
        elif rr >= 2.0:
            score += 0.08

        # 2. Strategy Alignment (25% Weight)
        notes = getattr(analysis, 'setup_notes', [])
        has_ema = any("EMA Trend" in n or "EMA Confirmation" in n for n in notes)
        has_reversal = any("Relative High/Low" in n for n in notes)
        if has_ema and has_reversal:
            score += 0.25
        elif has_ema or has_reversal:
            score += 0.15

        # 3. Channel direction (20% Weight — Rising channel is strongest signal)
        channel_direction = getattr(analysis, 'channel_direction', 'Flat')
        if channel_direction == "Rising":
            score += 0.20
        elif channel_direction == "Flat":
            score += 0.08
        # Falling: 0 points

        # 4. Multi-timeframe weekly confirmation (15% Weight)
        weekly_ema20 = getattr(analysis, 'weekly_ema20', None)
        weekly_ema50 = getattr(analysis, 'weekly_ema50', None)
        if weekly_ema20 and weekly_ema50 and weekly_ema20 > weekly_ema50:
            score += 0.15

        # 5. Channel Bot + HVN convergence bonus (5% Weight)
        if any("Strong Support" in n for n in notes):
            score += 0.05

        # 6. Channel breakout bonus (5% Weight)
        if any("Breakout" in n for n in notes):
            score += 0.05

        # 7. Trend Quality (remaining weight)
        trend = getattr(analysis, 'market_trend', 'Sideways')
        if "Uptrend" in trend:
            score += 0.05

        # 8. Earnings risk penalty
        if any("Earnings Risk" in n for n in notes):
            score = max(0, score - 0.15)

        # 9. Rejection Check
        if any("❌ Rejected" in n for n in notes):
            if score > 0.4: score = 0.4
            else: score *= 0.5

        return min(1.0, score)
