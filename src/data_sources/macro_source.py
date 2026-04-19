import yfinance as yf
import pandas as pd
import asyncio
import streamlit as st
from typing import Dict, Any, Optional, List
from src.config.market_config import TICKER_CONFIG

class MacroSource:
    """Source for global market indicators (Yields, VIX, Crypto, etc.)"""
    
    # Centralized configuration now handled by TICKER_CONFIG in src.config.market_config
    
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
    @st.cache_data(ttl=300)
    def fetch_global_snapshot() -> List[Dict[str, Any]]:
        """
        Fetches multiple global indices and crypto assets in parallel.
        Returns a list of dicts with metrics and geo-coordinates.
        """
        async def fetch_all():
            async def fetch_one(ticker: str, info: Dict[str, Any]):
                try:
                    import yfinance as yf
                    t = yf.Ticker(ticker)
                    # Use a thread for the blocking yfinance call
                    loop = asyncio.get_event_loop()
                    hist = await loop.run_in_executor(None, t.history, '5d')
                    
                    if not hist.empty:
                        curr = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist) > 1 else curr
                        pct = ((curr - prev) / prev) * 100 if prev != 0 else 0
                        
                        return {
                            'name': info['name'],
                            'short': info.get('short', info['name']),
                            'value': curr,
                            'pct_change': pct,
                            'type': info.get('type', 'Index'),
                            'lat': info.get('lat'),
                            'lon': info.get('lon'),
                            'country': info.get('country')
                        }
                except Exception as e:
                    print(f"Error fetching {info.get('name', ticker)}: {e}")
                return None

            tasks = [fetch_one(t, info) for t, info in TICKER_CONFIG.items()]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r]

        # Use new_event_loop for compatibility with Streamlit's threading model
        try:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(fetch_all())
        except:
            return asyncio.run(fetch_all())

    @staticmethod
    def fetch_sector_data() -> Dict[str, float]:
        """Fetch daily performance for all major sectors"""
        sector_perf = {}
        import yfinance as yf
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
    def fetch_historical_macro(ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch historical data for a specific macro indicator"""
        import yfinance as yf
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            return hist if not hist.empty else None
        except Exception as e:
            print(f"Error fetching historical macro data for {ticker}: {e}")
            return None
