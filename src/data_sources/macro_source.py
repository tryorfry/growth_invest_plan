"""Macro-economic data source using yfinance"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class MacroSource:
    """Source for global market indicators (Yields, VIX, etc.)"""
    
    TICKERS = {
        '10Y_Yield': '^TNX',
        '5Y_Yield': '^FVX',
        'Short_Yield': '^IRX',
        'VIX': '^VIX',
        'SPY': 'SPY',
        'Dollar_Index': 'DX-Y.NYB'
    }
    
    SECTOR_ETFS = {
        'Technology': 'XLK',
        'Health Care': 'XLV',
        'Financials': 'XLF',
        'Discretionary': 'XLY',
        'Communication': 'XLC',
        'Industrials': 'XLI',
        'Energy': 'XLE',
        'Materials': 'XLB',
        'Staples': 'XLP',
        'Utilities': 'XLU',
        'Real Estate': 'XLRE'
    }
    
    @staticmethod
    def fetch_macro_data() -> Dict[str, Any]:
        """Fetch current macro indicators and recent trends"""
        data = {}
        
        try:
            # Fetch current values
            for key, ticker in MacroSource.TICKERS.items():
                t = yf.Ticker(ticker)
                # Get the most recent price (end of day or current)
                hist = t.history(period='5d')
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - prev
                    
                    data[key] = {
                        'value': current,
                        'change': change,
                        'pct_change': (change / prev) * 100 if prev != 0 else 0,
                        'symbol': ticker
                    }
            
            # Add Yield Curve Calculation (10Y - Short)
            if '10Y_Yield' in data and 'Short_Yield' in data:
                data['Yield_Spread'] = {
                    'value': data['10Y_Yield']['value'] - data['Short_Yield']['value'],
                    'label': "10Y - 3M Spread"
                }
                
            return data
            
        except Exception as e:
            print(f"Error fetching macro data: {e}")
            return {}

    @staticmethod
    def fetch_sector_data() -> Dict[str, float]:
        """Fetch daily performance for all major sectors"""
        sector_perf = {}
        try:
            for name, ticker in MacroSource.SECTOR_ETFS.items():
                t = yf.Ticker(ticker)
                hist = t.history(period='2d')
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    perf = ((current - prev) / prev) * 100
                    sector_perf[name] = perf
            return sector_perf
        except Exception as e:
            print(f"Error fetching sector data: {e}")
            return {}

    @staticmethod
    def fetch_historical_macro(key: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch historical data for a specific macro indicator"""
        ticker = MacroSource.TICKERS.get(key)
        if not ticker:
            return None
            
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            return hist if not hist.empty else None
        except Exception as e:
            print(f"Error fetching historical macro data for {key}: {e}")
            return None
