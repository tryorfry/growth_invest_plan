"""Source for analyzing post-earnings price drift"""

import yfinance as yf
import pandas as pd
import streamlit as st
import requests
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from .base import DataSource

class EarningsSource(DataSource):
    """Analyzes historical stock performance following earnings reports"""

    def get_source_name(self) -> str:
        return "EarningsDrift"

    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Asynchronous wrapper for fetch_earnings_drift"""
        import asyncio
        loop = asyncio.get_running_loop()
        limit = kwargs.get('limit', 12)
        return await loop.run_in_executor(None, self.fetch_earnings_drift, ticker, limit)
    
    @st.cache_data(ttl=3600)
    def fetch_earnings_drift(_self, ticker: str, limit: int = 12) -> Dict[str, Any]:
        """
        Fetches historical earnings dates and calculates the T+1 and T+14 day returns.
        
        Args:
            ticker: Stock symbol to analyze.
            limit: Maximum number of past earnings events to analyze.
            
        Returns:
            Dict containing average drift statistics and the list of historical events.
        """
        try:
            stock = yf.Ticker(ticker)
            
            # 1. Get earnings dates
            try:
                calendar = stock.get_earnings_dates(limit=limit)
            except Exception as e:
                print(f"yfinance get_earnings_dates failed for {ticker}: {e}")
                calendar = _self._scrape_fallback_calendar(ticker, limit)
            
            if calendar is None or calendar.empty:
                # One last try via calendar property if get_earnings_dates failed
                try:
                    cal = stock.calendar
                    if cal and 'Earnings Date' in cal:
                        # This only gives future usually, so not useful for history drift
                        pass
                except: pass
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
                
            # yfinance returns future and past dates, we only want past
            try:
                tz_info = calendar.index.tz
            except AttributeError:
                tz_info = None
                
            now = pd.Timestamp.now(tz=tz_info) if tz_info else pd.Timestamp.now()
            calendar = calendar[calendar.index < now]
            
            if calendar.empty:
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
            
            # Need to download sufficient historical data to check T+14 for all dates
            # Grab last 4 years just to be safe
            try:
                history = stock.history(period="4y")
            except Exception as e:
                print(f"yfinance history failed for {ticker}: {e}")
                history = None
            
            if history is None or history.empty:
                # Fallback: Manual fetch of price history using robust mechanism
                print(f"Attempting manual price history fallback for {ticker}")
                url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range=5y&interval=1d"
                try:
                    r = _self._get_response_sync(url)
                    if r and r.status_code == 200:
                        data = r.json()
                        result = data.get('chart', {}).get('result', [{}])[0]
                        if result:
                            timestamps = result.get('timestamp')
                            quote_data = result.get('indicators', {}).get('quote', [None])[0]
                            if timestamps and quote_data:
                                history = pd.DataFrame({
                                    'Open': quote_data.get('open', []),
                                    'High': quote_data.get('high', []),
                                    'Low': quote_data.get('low', []),
                                    'Close': quote_data.get('close', []),
                                    'Volume': quote_data.get('volume', [])
                                }, index=pd.to_datetime(timestamps, unit='s', utc=True))
                                history.index = history.index.tz_convert('America/New_York')
                except Exception as ef:
                    print(f"Manual price history fallback failed for {ticker}: {ef}")
                    history = None
            
            if history is None or history.empty:
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
                
            history.index = history.index.tz_convert(None).normalize()
            
            events = []
            
            for edate, row in calendar.iterrows():
                if edate is None: continue
                
                # Normalize the timezone-aware earnings date to naive date for matching
                try:
                    e_date_naive = pd.Timestamp(edate).tz_localize(None).normalize()
                except Exception:
                    e_date_naive = pd.Timestamp(edate).normalize()
                
                # Find the index of the earnings date in the historical prices
                try:
                    # Sometime earnings are reported on weekends/holidays, find closest following trading day
                    future_dates = history.index[history.index >= e_date_naive]
                    if len(future_dates) == 0:
                        continue
                        
                    t0_loc = history.index.get_loc(future_dates[0])
                    
                    # We need the close BEFORE earnings (t-1) to calculate gap/drift correctly
                    if t0_loc == 0:
                        continue
                        
                    t_minus_1_price = history.iloc[t0_loc - 1].get('Close')
                    t_0_price = history.iloc[t0_loc].get('Close')
                    
                    if t_minus_1_price is None or t_0_price is None:
                        continue
                        
                    # Ensure we have data for T+1 and T+14
                    if t0_loc + 1 >= len(history):
                        # Still drifting, T+1 hasn't finished
                        continue
                        
                    t_1_price = history.iloc[t0_loc + 1].get('Close')
                    if t_1_price is None: continue
                    
                    # If T+14 doesn't exist yet, use the latest available price up to T+14
                    t_14_loc = min(t0_loc + 14, len(history) - 1)
                    t_14_price = history.iloc[t_14_loc].get('Close')
                    if t_14_price is None: continue
                    
                    # Calculate returns (%)
                    ret_t0 = ((t_0_price - t_minus_1_price) / t_minus_1_price) * 100    # Day of earnings reaction
                    ret_t1 = ((t_1_price - t_0_price) / t_0_price) * 100                # The "Drift" on Day 1
                    ret_t14 = ((t_14_price - t_0_price) / t_0_price) * 100              # The "Drift" by Day 14
                    
                    # Get estimated EPS and reported EPS
                    eps_est = row.get('EPS Estimate', None)
                    eps_rep = row.get('Reported EPS', None)
                    
                    beat = False
                    if pd.notna(eps_est) and pd.notna(eps_rep) and eps_rep > eps_est:
                        beat = True
                        
                    events.append({
                        "date": e_date_naive.strftime('%Y-%m-%d'),
                        "t0_return": ret_t0,
                        "t1_return": ret_t1,
                        "t14_return": ret_t14,
                        "eps_estimate": eps_est if pd.notna(eps_est) else None,
                        "eps_reported": eps_rep if pd.notna(eps_rep) else None,
                        "beat": beat
                    })
                    
                except KeyError:
                    # Date not in index, skip
                    pass
                    
            if not events:
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
                
            # Aggregate stats
            events_df = pd.DataFrame(events)
            avg_t1 = events_df['t1_return'].mean()
            avg_t14 = events_df['t14_return'].mean()
            win_rate_14 = (events_df['t14_return'] > 0).mean() * 100
            
            return {
                "analyzed_events": len(events),
                "avg_t0_return": events_df['t0_return'].mean(),
                "avg_t1_return": avg_t1,
                "avg_t14_return": avg_t14,
                "win_rate_t14_pct": win_rate_14,
                "events": events
            }

        except Exception as e:
            print(f"Error fetching earnings drift data for {ticker}: {e}")
            return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0, "error": str(e)}

    def _scrape_fallback_calendar(self, ticker: str, limit: int = 12) -> Optional[pd.DataFrame]:
        """Manual fallback scraper for Yahoo Finance earnings calendar"""
        url = f"https://finance.yahoo.com/calendar/earnings?symbol={ticker}"
        try:
            # Use robust request with SSL fallback
            html = self._get_response_sync(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html.content, 'html.parser')
            table = soup.find('table', {'data-test': 'calendar-table'})
            if not table:
                # Try finding any table if the test ID changed
                table = soup.find('table')
                if not table: return None
            
            data = []
            rows = table.find_all('tr')
            for row in rows[1:]: # Skip header
                cols = row.find_all('td')
                if len(cols) < 5: continue
                
                try:
                    # Column mapping: Symbol, Company, Earnings Date, EPS Estimate, Reported EPS, Surprise (%)
                    date_str = cols[2].get_text(strip=True)
                    if not date_str: continue
                    
                    # Robust cleanup for timezone strings that pandas might reject
                    clean_date = date_str
                    for tz in [' ET', ' EST', ' EDT', ' AM', ' PM', ' AM ET', ' PM ET']:
                        clean_date = clean_date.replace(tz, '')
                    
                    # Try to get just "Month Day, Year" or "Year-Month-Day"
                    match = re.search(r'([A-Za-z]+ \d+, \d{4})|(\d{4}-\d{2}-\d{2})', clean_date)
                    if match:
                        final_date_str = match.group(0)
                    else:
                        # Fallback: try split if regex failed
                        parts = clean_date.split(',')
                        if len(parts) >= 2:
                            final_date_str = parts[0] + ',' + parts[1]
                        else:
                            final_date_str = clean_date
                        
                    edate = pd.to_datetime(final_date_str, errors='coerce')
                    if pd.isna(edate): continue
                    
                    eps_est = cols[3].get_text(strip=True)
                    eps_rep = cols[4].get_text(strip=True)
                    
                    data.append({
                        "Earnings Date": edate,
                        "EPS Estimate": float(eps_est) if eps_est and eps_est != '-' else None,
                        "Reported EPS": float(eps_rep) if eps_rep and eps_rep != '-' else None
                    })
                except Exception as e:
                    continue
            
            if not data:
                return None
                
            df = pd.DataFrame(data)
            df.set_index("Earnings Date", inplace=True)
            df.sort_index(ascending=False, inplace=True)
            return df.head(limit)
            
        except Exception as e:
            print(f"Manual earnings fallback failed for {ticker}: {e}")
            return None
