"""YFinance data source for analyst price targets"""

import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional
import statistics
from datetime import datetime

from .base import AnalystDataSource


class YFinanceAnalystSource(AnalystDataSource):
    """Fetches analyst price targets using yfinance upgrades/downgrades data"""
    
    def get_source_name(self) -> str:
        return "YFinance (Analyst)"
    
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch analyst price targets from yfinance asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            **kwargs: Can include 'last_earnings_date' (pd.Timestamp)
            
        Returns:
            Dictionary with median price target or None
        """
        import asyncio
        loop = asyncio.get_running_loop()
        last_earnings_date = kwargs.get('last_earnings_date')
        
        return await loop.run_in_executor(
            None, 
            self._fetch_sync, 
            ticker, 
            last_earnings_date
        )

    def _fetch_sync(self, ticker: str, last_earnings_date: Optional[pd.Timestamp]) -> Optional[Dict[str, Any]]:
        """Synchronous fetch logic for yfinance data"""
        try:
            stock = yf.Ticker(ticker)
            
            # 1. Try upgrades_downgrades for historical targets (to filter by earnings)
            df = stock.upgrades_downgrades
            
            if df is not None and not df.empty and last_earnings_date is not None:
                # Ensure index is datetime and localized if last_earnings_date is localized
                if last_earnings_date.tzinfo is not None:
                    if df.index.tz is None:
                        df.index = df.index.tz_localize('UTC').tz_convert(last_earnings_date.tzinfo)
                    else:
                        df.index = df.index.tz_convert(last_earnings_date.tzinfo)
                else:
                    if df.index.tz is not None:
                        df.index = df.index.tz_convert(None)
                
                # Filter ratings after earnings
                recent_ratings = df[df.index >= last_earnings_date]
                
                # Extract price targets
                targets = []
                if 'currentPriceTarget' in recent_ratings.columns:
                    targets = recent_ratings['currentPriceTarget'].dropna().tolist()
                
                if targets:
                    median_target = statistics.median(targets)
                    return {"median_price_target": float(median_target)}
            
            # 2. Fallback: Use yfinance consensus median from info (if no historical breakdown or filter failed)
            info = stock.info
            median_target = info.get('targetMedianPrice')
            
            if median_target is not None:
                return {"median_price_target": float(median_target)}
                
            return None
            
        except Exception as e:
            print(f"Error fetching YFinance analyst data for {ticker}: {e}")
            return None
