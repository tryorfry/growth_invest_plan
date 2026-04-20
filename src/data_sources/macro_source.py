import yfinance as yf
import pandas as pd
import asyncio
import streamlit as st
from typing import Dict, Any, Optional, List
from src.config.market_config import TICKER_CONFIG
from .base import DataSource

class MacroSource(DataSource):
    """Source for global market indicators (Yields, VIX, Crypto, etc.)"""
    
    MACRO_TICKER_MAP = {
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

    def get_source_name(self) -> str:
        return "MarketPulse"

    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Default fetch returns the global snapshot"""
        return {"snapshot": await self.fetch_global_snapshot_async()}

    @st.cache_data(ttl=300)
    def fetch_global_snapshot(_self) -> List[Dict[str, Any]]:
        """Sync wrapper for global snapshot fetching"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_self.fetch_global_snapshot_async())
        except Exception as e:
            print(f"Async snapshot failed: {e}")
            return []

    async def fetch_global_snapshot_async(_self) -> List[Dict[str, Any]]:
        """Fetches multiple global indices and crypto assets in parallel."""
        async def fetch_one(ticker: str, info: Dict[str, Any]):
            hist = None
            try:
                import yfinance as yf
                t = yf.Ticker(ticker)
                loop = asyncio.get_event_loop()
                hist = await loop.run_in_executor(None, lambda: t.history(period='5d'))
            except Exception as e:
                print(f"yfinance failed for {ticker}: {e}")

            # Fallback if yfinance failed (SSL or other)
            if hist is None or hist.empty:
                url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
                resp = _self._get_response_sync(url)
                if resp and resp.status_code == 200:
                    data = resp.json()
                    result = data.get('chart', {}).get('result', [{}])[0]
                    if result and 'timestamp' in result:
                        ts = result['timestamp']
                        close = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        if ts and close:
                            hist = pd.DataFrame({'Close': close}, index=pd.to_datetime(ts, unit='s'))

            if hist is not None and not hist.empty:
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
            return None

        # TICKER_CONFIG from market_config
        from src.config.market_config import TICKER_CONFIG
        tasks = [fetch_one(t, info) for t, info in TICKER_CONFIG.items()]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    @st.cache_data(ttl=600)
    def fetch_macro_data(_self) -> Dict[str, Any]:
        """Fetches core macro indicators (yields, vix, dxy) in parallel."""
        async def fetch_all_macro():
            async def fetch_one(key: str, ticker: str):
                hist = None
                try:
                    import yfinance as yf
                    t = yf.Ticker(ticker)
                    loop = asyncio.get_event_loop()
                    hist = await loop.run_in_executor(None, lambda: t.history(period='5d'))
                except Exception: pass

                if hist is None or hist.empty:
                    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
                    resp = _self._get_response_sync(url)
                    if resp and resp.status_code == 200:
                        data = resp.json()
                        result = data.get('chart', {}).get('result', [{}])[0]
                        if result and 'timestamp' in result:
                            close = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                            if close: hist = pd.DataFrame({'Close': close})

                if hist is not None and not hist.empty:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else curr
                    pct = ((curr - prev) / prev) * 100 if (prev and prev != 0) else 0
                    return key, {"value": curr, "pct_change": pct}
                return key, None

            tasks = [fetch_one(key, ticker) for key, ticker in _self.MACRO_TICKER_MAP.items()]
            results = await asyncio.gather(*tasks)
            data = {k: v for k, v in results if v}
            
            if '10Y_Yield' in data and 'Short_Yield' in data:
                data['Yield_Spread'] = {"value": data['10Y_Yield']['value'] - data['Short_Yield']['value']}
            return data

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(fetch_all_macro())
        except Exception:
            return {}

    @st.cache_data(ttl=600)
    def fetch_sector_data(_self) -> Dict[str, float]:
        """Fetch daily performance for all major sectors in parallel"""
        async def fetch_all_sectors():
            async def fetch_one(name: str, ticker: str):
                hist = None
                try:
                    import yfinance as yf
                    t = yf.Ticker(ticker)
                    loop = asyncio.get_event_loop()
                    hist = await loop.run_in_executor(None, lambda: t.history(period='2d'))
                except Exception: pass

                if (hist is None or hist.empty) or len(hist) < 2:
                    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range=2d&interval=1d"
                    resp = _self._get_response_sync(url)
                    if resp and resp.status_code == 200:
                        data = resp.json()
                        result = data.get('chart', {}).get('result', [{}])[0]
                        if result and 'timestamp' in result:
                            close = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                            if len(close) >= 2: hist = pd.DataFrame({'Close': close})

                if hist is not None and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    return name, ((current - prev) / prev) * 100
                return name, None

            tasks = [fetch_one(name, ticker) for name, ticker in _self.SECTOR_ETFS.items()]
            results = await asyncio.gather(*tasks)
            return {k: v for k, v in results if v is not None}

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(fetch_all_sectors())
        except Exception:
            return {}

    def fetch_historical_macro(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        symbol = self.MACRO_TICKER_MAP.get(ticker, ticker)
        import yfinance as yf
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period=period)
            if not hist.empty: return hist
        except Exception: pass
        
        # Fallback
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval=1d"
        resp = self._get_response_sync(url)
        if resp and resp.status_code == 200:
            data = resp.json()
            result = data.get('chart', {}).get('result', [{}])[0]
            if result and 'timestamp' in result:
                ts = result['timestamp']
                close = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                if ts and close:
                    return pd.DataFrame({'Close': close}, index=pd.to_datetime(ts, unit='s'))
        return None
