"""YFinance data source for analyst price targets and upgrade/downgrade actions"""

import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional
import statistics
from datetime import datetime

from .base import AnalystDataSource


class YFinanceAnalystSource(AnalystDataSource):
    """Fetches analyst price targets and recent upgrade/downgrade from yfinance"""
    
    def get_source_name(self) -> str:
        return "YFinance (Analyst)"
    
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch analyst price targets and recent action from yfinance.
        
        Args:
            ticker: Stock ticker symbol
            **kwargs: Can include 'last_earnings_date' (pd.Timestamp)
            
        Returns:
            Dictionary with median_price_target and recent_action or None
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
            result = {}
            
            # --- 1. Analyst price target (most reliable: use consensus median directly) ---
            try:
                apt = stock.analyst_price_targets  # dict: current, high, low, mean, median
                if isinstance(apt, dict) and apt.get('median'):
                    result['median_price_target'] = float(apt['median'])
            except Exception:
                pass
            
            # Fallback: use info.targetMedianPrice if analyst_price_targets unavailable
            if 'median_price_target' not in result:
                try:
                    info = stock.info
                    median_target = info.get('targetMedianPrice')
                    if median_target is not None:
                        result['median_price_target'] = float(median_target)
                except Exception:
                    pass
            
            # --- 2. Recent analyst upgrade/downgrade action ---
            try:
                df = stock.upgrades_downgrades
                
                if df is not None and not df.empty:
                    # Normalize timezone for comparison
                    if last_earnings_date is not None:
                        if last_earnings_date.tzinfo is not None:
                            if df.index.tz is None:
                                df.index = df.index.tz_localize('UTC').tz_convert(last_earnings_date.tzinfo)
                            else:
                                df.index = df.index.tz_convert(last_earnings_date.tzinfo)
                        else:
                            if df.index.tz is not None:
                                df.index = df.index.tz_convert(None)
                        
                        # Only ratings post most recent earnings
                        recent_df = df[df.index >= last_earnings_date].copy()
                    else:
                        # No earnings date: use last 90 days
                        cutoff = pd.Timestamp.now(tz=df.index.tz if df.index.tz else None) - pd.Timedelta(days=90)
                        recent_df = df[df.index >= cutoff].copy()
                    
                    if not recent_df.empty:
                        # Most recent row
                        latest = recent_df.iloc[0]
                        firm = latest.get('Firm', '') if hasattr(latest, 'get') else ''
                        action = latest.get('Action', '') if hasattr(latest, 'get') else ''
                        to_grade = latest.get('ToGrade', '') if hasattr(latest, 'get') else ''
                        
                        # Build human-readable label e.g. "Morgan Stanley: Upgraded → Buy"
                        if firm or action or to_grade:
                            parts = []
                            if firm:
                                parts.append(str(firm))
                            if action:
                                parts.append(str(action))
                            if to_grade:
                                parts.append(f"→ {to_grade}")
                            result['recent_action'] = ' '.join(parts)
                        
                        # Also compute median from post-earnings price targets if available
                        if 'median_price_target' not in result and 'currentPriceTarget' in recent_df.columns:
                            targets = recent_df['currentPriceTarget'].dropna().tolist()
                            if targets:
                                result['median_price_target'] = float(statistics.median(targets))
            except Exception as e:
                print(f"Error fetching upgrades/downgrades for {ticker}: {e}")
            
            return result if result else None
            
        except Exception as e:
            print(f"Error fetching YFinance analyst data for {ticker}: {e}")
            return None
