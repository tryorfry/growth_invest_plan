import yfinance as yf
import pandas as pd
import asyncio
import streamlit as st
from typing import Dict, Any, Optional, List
from src.config.market_config import TICKER_CONFIG
from .base import DataSource


# ===========================================================================
# MODULE-LEVEL CACHED FUNCTIONS
# ===========================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_global_snapshot() -> List[Dict[str, Any]]:
    """Fetch global market snapshot. Cached 5 min."""
    return MacroSource()._fetch_global_snapshot_sync()


@st.cache_data(ttl=600, show_spinner=False)
def get_macro_data() -> Dict[str, Any]:
    """Fetch core macro indicators (yields, VIX, DXY). Cached 10 min."""
    return MacroSource()._fetch_macro_data_sync()


@st.cache_data(ttl=600, show_spinner=False)
def get_sector_data() -> Dict[str, float]:
    """Fetch daily sector ETF performance. Cached 10 min."""
    return MacroSource()._fetch_sector_data_sync()


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

    # ------------------------------------------------------------------
    # Sync wrappers for st.cache_data
    # ------------------------------------------------------------------

    def _fetch_global_snapshot_sync(self) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.fetch_global_snapshot_async())
        except Exception as e:
            print(f"Async snapshot failed: {e}")
            return []

    def _fetch_macro_data_sync(self) -> Dict[str, Any]:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._fetch_batch_data_async(list(self.MACRO_TICKER_MAP.values()), period='5d'))
        except Exception:
            return {}

    def _fetch_sector_data_sync(self) -> Dict[str, float]:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            raw_data = loop.run_until_complete(self._fetch_batch_data_async(list(self.SECTOR_ETFS.values()), period='2d'))
            
            # Map back to names
            results = {}
            ticker_to_name = {v: k for k, v in self.SECTOR_ETFS.items()}
            for ticker, data in raw_data.items():
                name = ticker_to_name.get(ticker)
                if name and 'pct_change' in data:
                    results[name] = data['pct_change']
            return results
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Optimized Async Fetching Logic
    # ------------------------------------------------------------------

    async def _fetch_batch_data_async(self, tickers: List[str], period: str = '5d') -> Dict[str, Dict[str, Any]]:
        """
        Fetches multiple tickers in a single batch using yf.download.
        Falls back to individual async fetches if batch fails.
        """
        loop = asyncio.get_event_loop()
        results = {}

        try:
            # 🏎️ Batch Download (Single network request)
            df = await loop.run_in_executor(None, lambda: yf.download(
                tickers, period=period, interval='1d', group_by='ticker', progress=False, timeout=10
            ))
            
            if not df.empty:
                for ticker in tickers:
                    try:
                        # Handle both SingleIndex and MultiIndex dataframes from yf.download
                        if len(tickers) > 1:
                            ticker_df = df[ticker]
                        else:
                            ticker_df = df
                            
                        ticker_df = ticker_df.dropna(subset=['Close'])
                        if not ticker_df.empty and len(ticker_df) >= 1:
                            curr = ticker_df['Close'].iloc[-1]
                            prev = ticker_df['Close'].iloc[-2] if len(ticker_df) > 1 else curr
                            pct = ((curr - prev) / prev) * 100 if prev != 0 else 0
                            results[ticker] = {"value": curr, "pct_change": pct}
                    except Exception:
                        continue
        except Exception as e:
            print(f"Batch fetch failed: {e}. Falling back to individual fetches.")

        # 🎯 Individual Fallback for missing tickers
        missing = [t for t in tickers if t not in results]
        if missing:
            tasks = [self._fetch_single_ticker_async(t, period) for t in missing]
            fallback_results = await asyncio.gather(*tasks)
            for t, res in zip(missing, fallback_results):
                if res:
                    results[t] = res

        return results

    async def _fetch_single_ticker_async(self, ticker: str, period: str) -> Optional[Dict[str, Any]]:
        """Fetches a single ticker with async-safe fallback."""
        loop = asyncio.get_event_loop()
        hist = None
        
        # 1. yfinance
        try:
            t = yf.Ticker(ticker)
            hist = await loop.run_in_executor(None, lambda: t.history(period=period))
        except Exception:
            pass

        # 2. HTTP Fallback (wrapped in executor to avoid blocking loop)
        if hist is None or hist.empty:
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d"
            resp = await loop.run_in_executor(None, lambda: self._get_response_sync(url))
            if resp and resp.status_code == 200:
                try:
                    data = resp.json()
                    result = data.get('chart', {}).get('result', [{}])[0]
                    if result and 'timestamp' in result:
                        ts = result['timestamp']
                        close = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        if ts and close:
                            hist = pd.DataFrame({'Close': close}, index=pd.to_datetime(ts, unit='s'))
                except Exception:
                    pass

        if hist is not None and not hist.empty:
            hist = hist.dropna(subset=['Close'])
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else curr
                pct = ((curr - prev) / prev) * 100 if prev != 0 else 0
                return {"value": curr, "pct_change": pct}
        return None

    async def fetch_global_snapshot_async(self) -> List[Dict[str, Any]]:
        """Optimized global snapshot using batch fetching."""
        tickers = list(TICKER_CONFIG.keys())
        batch_results = await self._fetch_batch_data_async(tickers, period='5d')
        
        final_results = []
        for ticker, info in TICKER_CONFIG.items():
            res = batch_results.get(ticker)
            if res:
                final_results.append({
                    'name': info['name'],
                    'short': info.get('short', info['name']),
                    'value': res['value'],
                    'pct_change': res['pct_change'],
                    'type': info.get('type', 'Index'),
                    'lat': info.get('lat'),
                    'lon': info.get('lon'),
                    'country': info.get('country')
                })
        return final_results

    # ------------------------------------------------------------------
    # Backward Compatibility & Helpers
    # ------------------------------------------------------------------

    def fetch_global_snapshot(self) -> List[Dict[str, Any]]:
        return get_global_snapshot()

    def fetch_macro_data(self) -> Dict[str, Any]:
        return get_macro_data()

    def fetch_sector_data(self) -> Dict[str, float]:
        return get_sector_data()

    def _fetch_macro_data_sync_legacy(self) -> Dict[str, Any]:
        # Implementation moved to _fetch_batch_data_async
        return self._fetch_macro_data_sync()

    def fetch_historical_macro(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        symbol = self.MACRO_TICKER_MAP.get(ticker, ticker)
        # Simple sync wrapper for historical charts
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period=period)
            if not hist.empty:
                return hist
        except Exception:
            pass
        return None
