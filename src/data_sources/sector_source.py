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
        Fetches the 1W, 1M, 3M, 6M, and 1Y performance for all sectors compared to SPY.
        Returns a sorted list of dictionaries with weighted Relative Strength scores.
        """
        tickers = list(self.SECTORS.values()) + ["SPY"]
        
        try:
            # Download 13 months of data to safely calculate 1Y returns
            data = yf.download(tickers, period="14mo", interval="1d", group_by="ticker", auto_adjust=True, progress=False)
            
            results = []
            spy_close = data['SPY']['Close'].dropna()
            
            for name, symbol in self.SECTORS.items():
                if symbol in data and not data[symbol].empty:
                    df = data[symbol]['Close'].dropna()
                    
                    if len(df) >= 252: # 1 year of trading days
                        current = df.iloc[-1]
                        
                        # Calculate returns (%)
                        ret_1w = ((current - df.iloc[-6]) / df.iloc[-6]) * 100 if len(df) >= 6 else 0
                        ret_1m = ((current - df.iloc[-22]) / df.iloc[-22]) * 100 if len(df) >= 22 else 0
                        ret_3m = ((current - df.iloc[-64]) / df.iloc[-64]) * 100 if len(df) >= 64 else 0
                        ret_6m = ((current - df.iloc[-126]) / df.iloc[-126]) * 100 if len(df) >= 126 else 0
                        ret_1y = ((current - df.iloc[-252]) / df.iloc[-252]) * 100 if len(df) >= 252 else 0
                        
                        # Calculate SPY returns for relative performance
                        spy_curr = spy_close.iloc[-1]
                        spy_1y = ((spy_curr - spy_close.iloc[-252]) / spy_close.iloc[-252]) * 100 if len(spy_close) >= 252 else 0
                        
                        # Weighted Relative Strength (IBD Style: 40% 3M, 20% 6M, 20% 9M, 20% 12M)
                        # Simplified here as we don't have 9M explicitly yet: 40% 3M, 30% 6M, 30% 12M
                        rs_score = (ret_3m * 0.4) + (ret_6m * 0.3) + (ret_1y * 0.3)
                        
                        results.append({
                            "Sector": name,
                            "Ticker": symbol,
                            "1W Return": ret_1w,
                            "1M Return": ret_1m,
                            "3M Return": ret_3m,
                            "6M Return": ret_6m,
                            "1Y Return": ret_1y,
                            "RS Score": rs_score,
                            "Relative to SPY (1Y)": ret_1y - spy_1y
                        })
            
            # Sort by RS Score descending
            return sorted(results, key=lambda x: x['RS Score'], reverse=True)
        except Exception as e:
            print(f"Error fetching sector data: {e}")
            return []
