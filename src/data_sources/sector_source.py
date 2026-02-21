"""Source for Sector Rotation and Relative Strength Data"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, List

class SectorSource:
    """Fetches and calculates performance for the 11 major SPDR Sector ETFs"""
    
    # Standard SPDR ETF mapping
    SECTORS = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Consumer Discretionary": "XLY",
        "Communication Services": "XLC",
        "Industrials": "XLI",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Materials": "XLB"
    }
    
    def fetch_sector_performance(self) -> List[Dict[str, Any]]:
        """
        Fetches the 1W, 1M, and 3M performance for all sectors compared to SPY.
        Returns a sorted list of dictionaries.
        """
        tickers = list(self.SECTORS.values()) + ["SPY"]
        
        try:
            # Download 4 months of data to safely calculate 3M returns
            data = yf.download(tickers, period="4mo", interval="1d", group_by="ticker", auto_adjust=True, progress=False)
            
            results = []
            
            for name, symbol in self.SECTORS.items():
                if symbol in data and not data[symbol].empty:
                    df = data[symbol]['Close'].dropna()
                    
                    if len(df) >= 63: # roughly 3 months of trading days
                        current = df.iloc[-1]
                        
                        # Calculate returns (%)
                        ret_1w = ((current - df.iloc[-6]) / df.iloc[-6]) * 100 if len(df) >= 6 else 0
                        ret_1m = ((current - df.iloc[-22]) / df.iloc[-22]) * 100 if len(df) >= 22 else 0
                        ret_3m = ((current - df.iloc[-64]) / df.iloc[-64]) * 100 if len(df) >= 64 else 0
                        
                        results.append({
                            "Sector": name,
                            "Ticker": symbol,
                            "1W Return": ret_1w,
                            "1M Return": ret_1m,
                            "3M Return": ret_3m
                        })
            
            return results
        except Exception as e:
            print(f"Error fetching sector data: {e}")
            return []
