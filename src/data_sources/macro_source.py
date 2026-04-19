import yfinance as yf
import pandas as pd
import asyncio
from typing import Dict, Any, Optional

class MacroSource:
    """Source for global market indicators (Yields, VIX, Crypto, etc.)"""
    
    TICKERS = {
        '10Y_Yield': '^TNX',
        '5Y_Yield': '^FVX',
        'Short_Yield': '^IRX',
        'VIX': '^VIX',
        'SPY': 'SPY',
        'Dollar_Index': 'DX-Y.NYB'
    }

    SNAPSHOT_CONFIG = {
        'S&P 500': '^GSPC',
        'Nasdaq': '^IXIC',
        'FTSE 100': '^FTSE',
        'DAX 40': '^GDAXI',
        'Nikkei 225': '^N225',
        'Hang Seng': '^HSI',
        'Straits Times': '^STI',
        'Nifty 50': '^NSEI',
        'ASX 200': '^AXJO',
        'Bitcoin': 'BTC-USD',
        'Ethereum': 'ETH-USD'
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
        """Fetch current macro indicators and recent trends (Sync for legacy support)"""
        data = {}
        try:
            for key, ticker in MacroSource.TICKERS.items():
                t = yf.Ticker(ticker)
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
    async def fetch_global_snapshot() -> List[Dict[str, Any]]:
        """Parallel fetch for global performance cards (Async)"""
        async def fetch_one(name: str, ticker: str):
            try:
                # Use a small loop to run yfinance in a thread to keep it async-friendly
                loop = asyncio.get_event_loop()
                t = yf.Ticker(ticker)
                hist = await loop.run_in_executor(None, t.history, '5d')
                if not hist.empty:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else curr
                    pct = ((curr - prev) / prev) * 100
                    return {
                        'name': name,
                        'value': curr,
                        'pct_change': pct,
                        'type': 'Crypto' if 'USD' in ticker else 'Index'
                    }
            except Exception as e:
                print(f"Error fetching {name}: {e}")
            return None

        tasks = [fetch_one(n, t) for n, t in MacroSource.SNAPSHOT_CONFIG.items()]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

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
        if not ticker: return None
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            return hist if not hist.empty else None
        except Exception as e:
            print(f"Error fetching historical macro data for {key}: {e}")
            return None
