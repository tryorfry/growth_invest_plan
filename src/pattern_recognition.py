"""Candlestick pattern recognition"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


class PatternRecognition:
    """Detect candlestick patterns in price data"""
    
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect candlestick patterns in historical data.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected patterns with dates and types
        """
        patterns = []
        
        for i in range(1, len(df)):
            # Get current and previous candles
            curr = df.iloc[i]
            prev = df.iloc[i-1] if i > 0 else None
            
            # Doji pattern
            if self._is_doji(curr):
                patterns.append({
                    'date': df.index[i],
                    'pattern': 'Doji',
                    'signal': 'Neutral/Reversal',
                    'price': curr['Close']
                })
            
            # Hammer pattern
            if prev is not None and self._is_hammer(curr, prev):
                patterns.append({
                    'date': df.index[i],
                    'pattern': 'Hammer',
                    'signal': 'Bullish Reversal',
                    'price': curr['Close']
                })
            
            # Shooting Star
            if prev is not None and self._is_shooting_star(curr, prev):
                patterns.append({
                    'date': df.index[i],
                    'pattern': 'Shooting Star',
                    'signal': 'Bearish Reversal',
                    'price': curr['Close']
                })
            
            # Engulfing patterns
            if prev is not None:
                if self._is_bullish_engulfing(curr, prev):
                    patterns.append({
                        'date': df.index[i],
                        'pattern': 'Bullish Engulfing',
                        'signal': 'Bullish Reversal',
                        'price': curr['Close']
                    })
                elif self._is_bearish_engulfing(curr, prev):
                    patterns.append({
                        'date': df.index[i],
                        'pattern': 'Bearish Engulfing',
                        'signal': 'Bearish Reversal',
                        'price': curr['Close']
                    })
        
        return patterns
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Detect Doji pattern"""
        body = abs(candle['Close'] - candle['Open'])
        range_val = candle['High'] - candle['Low']
        return body < (range_val * 0.1) if range_val > 0 else False
    
    def _is_hammer(self, candle: pd.Series, prev: pd.Series) -> bool:
        """Detect Hammer pattern"""
        body = abs(candle['Close'] - candle['Open'])
        lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
        upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
        
        # Hammer: small body, long lower shadow, little/no upper shadow
        if body > 0 and lower_shadow > (body * 2) and upper_shadow < body:
            # Should appear in downtrend
            return candle['Close'] < prev['Close']
        return False
    
    def _is_shooting_star(self, candle: pd.Series, prev: pd.Series) -> bool:
        """Detect Shooting Star pattern"""
        body = abs(candle['Close'] - candle['Open'])
        lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
        upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
        
        # Shooting Star: small body, long upper shadow, little/no lower shadow
        if body > 0 and upper_shadow > (body * 2) and lower_shadow < body:
            # Should appear in uptrend
            return candle['Close'] > prev['Close']
        return False
    
    def _is_bullish_engulfing(self, candle: pd.Series, prev: pd.Series) -> bool:
        """Detect Bullish Engulfing pattern"""
        # Previous candle is bearish
        prev_bearish = prev['Close'] < prev['Open']
        # Current candle is bullish
        curr_bullish = candle['Close'] > candle['Open']
        # Current candle engulfs previous
        engulfs = candle['Open'] < prev['Close'] and candle['Close'] > prev['Open']
        
        return prev_bearish and curr_bullish and engulfs
    
    def _is_bearish_engulfing(self, candle: pd.Series, prev: pd.Series) -> bool:
        """Detect Bearish Engulfing pattern"""
        # Previous candle is bullish
        prev_bullish = prev['Close'] > prev['Open']
        # Current candle is bearish
        curr_bearish = candle['Close'] < candle['Open']
        # Current candle engulfs previous
        engulfs = candle['Open'] > prev['Close'] and candle['Close'] < prev['Open']
        
        return prev_bullish and curr_bearish and engulfs
    
    def get_recent_patterns(self, df: pd.DataFrame, days: int = 30) -> List[Dict[str, Any]]:
        """Get patterns from the last N days"""
        all_patterns = self.detect_patterns(df)
        
        if not all_patterns:
            return []
        
        # Filter to recent patterns
        cutoff_date = df.index[-1] - pd.Timedelta(days=days)
        recent = [p for p in all_patterns if p['date'] >= cutoff_date]
        
        return recent
        
    def detect_relative_high_low(self, df: pd.DataFrame, window: int = 5) -> Dict[str, Any]:
        """
        Identify pivot highs and lows to determine HH/HL/LH/LL.
        Returns a dict with identified pivot points and trend assessment.
        """
        if df.empty or len(df) < window * 2:
            return {'pivots': [], 'trend': 'Neutral'}

        highs = df['High'].values
        lows = df['Low'].values
        pivots = []

        for i in range(window, len(df) - window):
            # Pivot High
            if all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, window+1)):
                pivots.append({'type': 'HH' if not pivots or pivots[-1]['price'] < highs[i] else 'LH', 
                               'price': float(highs[i]), 'date': df.index[i], 'pivot_type': 'High'})
            
            # Pivot Low
            if all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, window+1)):
                pivots.append({'type': 'HL' if not pivots or pivots[-1]['price'] < lows[i] else 'LL', 
                               'price': float(lows[i]), 'date': df.index[i], 'pivot_type': 'Low'})

        # Refine labels based on sequence
        last_high = None
        last_low = None
        for p in pivots:
            if p['pivot_type'] == 'High':
                if last_high is not None:
                    p['type'] = 'HH' if p['price'] > last_high else 'LH'
                last_high = p['price']
            else:
                if last_low is not None:
                    p['type'] = 'HL' if p['price'] > last_low else 'LL'
                last_low = p['price']

        # Determine trend
        trend = "Neutral"
        if len(pivots) >= 2:
            recent = pivots[-4:]
            hh_hl = any(p['type'] == 'HH' for p in recent) and any(p['type'] == 'HL' for p in recent)
            ll_lh = any(p['type'] == 'LL' for p in recent) and any(p['type'] == 'LH' for p in recent)
            
            if hh_hl: trend = "Uptrend"
            elif ll_lh: trend = "Downtrend"

        return {'pivots': pivots, 'trend': trend}

    def detect_downtrend_line_break(self, df: pd.DataFrame, lookback: int = 40) -> Dict[str, Any]:
        """
        Calculates a downtrend line from recent highs and checks for a close above it.
        """
        if len(df) < lookback:
            return {'setup': False, 'price': 0, 'line_value': 0}
            
        recent = df.iloc[-lookback:]
        # Find two major highs to form a line
        highs = recent['High'].values
        # Simple heuristic: find max and another high at least 10 days apart
        idx1 = np.argmax(highs)
        if idx1 > lookback - 15: # Max is too recent
             idx1 = np.argmax(highs[:-15])
             
        # Find second high after the first
        if idx1 < lookback - 10:
            idx2 = idx1 + 5 + np.argmax(highs[idx1+5:])
        else:
            idx2 = lookback - 1
            
        p1 = (idx1, highs[idx1])
        p2 = (idx2, highs[idx2])
        
        if p1[1] <= p2[1]: # Not a downtrend line
            return {'setup': False}
            
        # Line eq: y = mx + c
        m = (p2[1] - p1[1]) / (p2[0] - p1[0])
        c = p1[1] - m * p1[0]
        
        # Current line value at the last index (lookback - 1)
        line_val = m * (lookback - 1) + c
        curr_close = df.iloc[-1]['Close']
        
        return {
            'setup': curr_close > line_val,
            'price': float(curr_close),
            'line_value': float(line_val),
            'slope': float(m)
        }

    def detect_trend_patterns(self, df: pd.DataFrame, supports: List[float], resistances: List[float], days: int = 14) -> List[Dict[str, Any]]:

        """
        Detect macro/swing patterns: Bounces, Breakouts, and S/R Flips against horizontal levels.
        Returns a rich dictionary containing the isolated price slice for mini-chart plotting.
        """
        if df.empty or (not supports and not resistances):
            return []
            
        patterns = []
        # Look only at the recent N window for the triggering event
        cutoff_date = df.index[-1] - pd.Timedelta(days=days)
        recent_df = df[df.index >= cutoff_date]
        
        if recent_df.empty:
            return []
            
        buffer_pct = 0.015  # 1.5% interaction zone
        
        for level in supports:
            # 1. Support Bounce
            # Did price dip into support zone and close higher recently?
            for i in range(1, len(recent_df)):
                curr = recent_df.iloc[i]
                prev = recent_df.iloc[i-1]
                
                in_zone_curr = abs(curr['Low'] - level) / level <= buffer_pct
                in_zone_prev = abs(prev['Low'] - level) / level <= buffer_pct
                
                bullish_close = curr['Close'] > curr['Open'] and curr['Close'] > level
                
                if (in_zone_curr or in_zone_prev) and bullish_close:
                    # Capture the surrounding 20 days for plotting (10 before, 10 after)
                    curr_loc = df.index.get_loc(curr.name)
                    plot_start = max(0, curr_loc - 10)
                    plot_end = min(len(df), curr_loc + 10)
                    plot_slice = df.iloc[plot_start: plot_end]
                    
                    # Prepare plot data with a constant 'Level' line for distinct visual
                    plot_df = plot_slice[['Close']].copy()
                    plot_df['Level'] = float(level)
                    
                    patterns.append({
                        'date': curr.name,
                        'pattern': 'Support Bounce',
                        'level': level,
                        'signal': 'Bullish Swing',
                        'price': curr['Close'],
                        'plot_data': plot_df
                    })
                    break # Only flag the most recent distinct event per level
                    
        for level in resistances:
            # 2. Resistance Breakout / S/R Flip
            # Did price cross strongly above a resistance level it was previously below?
            for i in range(1, len(recent_df)):
                curr = recent_df.iloc[i]
                prev = recent_df.iloc[i-1]
                
                crossed_above = prev['Close'] < level and curr['Close'] > level
                strong_close = (curr['Close'] - level) / level > 0.005 # At least 0.5% above to confirm
                
                if crossed_above and strong_close:
                    curr_loc = df.index.get_loc(curr.name)
                    plot_start = max(0, curr_loc - 10)
                    plot_end = min(len(df), curr_loc + 10)
                    plot_slice = df.iloc[plot_start: plot_end]
                    
                    plot_df = plot_slice[['Close']].copy()
                    plot_df['Level'] = float(level)
                    
                    patterns.append({
                        'date': curr.name,
                        'pattern': 'Resistance Breakout (S/R Flip)',
                        'level': level,
                        'signal': 'Strong Bullish',
                        'price': curr['Close'],
                        'plot_data': plot_df
                    })
                    break
                    
            # 3. Resistance Rejection (Downtrend Swing)
            for i in range(1, len(recent_df)):
                curr = recent_df.iloc[i]
                prev = recent_df.iloc[i-1]
                
                in_zone_curr = abs(curr['High'] - level) / level <= buffer_pct
                in_zone_prev = abs(prev['High'] - level) / level <= buffer_pct
                
                bearish_close = curr['Close'] < curr['Open'] and curr['Close'] < level
                
                if (in_zone_curr or in_zone_prev) and bearish_close:
                    curr_loc = df.index.get_loc(curr.name)
                    plot_start = max(0, curr_loc - 10)
                    plot_end = min(len(df), curr_loc + 10)
                    plot_slice = df.iloc[plot_start: plot_end]
                    
                    plot_df = plot_slice[['Close']].copy()
                    plot_df['Level'] = float(level)
                    
                    patterns.append({
                        'date': curr.name,
                        'pattern': 'Resistance Rejection',
                        'level': level,
                        'signal': 'Bearish Swing',
                        'price': curr['Close'],
                        'plot_data': plot_df
                    })
                    break

        # Sort by most recent
        return sorted(patterns, key=lambda x: x['date'], reverse=True)
