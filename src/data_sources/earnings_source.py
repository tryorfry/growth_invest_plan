"""Source for analyzing post-earnings price drift"""

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, Any, List

class EarningsSource:
    """Analyzes historical stock performance following earnings reports"""
    
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
            calendar = stock.get_earnings_dates(limit=limit)
            
            if calendar is None or calendar.empty:
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
                
            # yfinance returns future and past dates, we only want past
            calendar = calendar[calendar.index < pd.Timestamp.now(tz=calendar.index.tz)]
            
            if calendar.empty:
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
            
            # Need to download sufficient historical data to check T+14 for all dates
            # Grab last 4 years just to be safe
            history = stock.history(period="4y")
            
            if history.empty:
                return {"analyzed_events": 0, "events": [], "avg_t1_return": 0.0, "avg_t14_return": 0.0}
                
            history.index = history.index.tz_convert(None).normalize()
            
            events = []
            
            for edate, row in calendar.iterrows():
                # Normalize the timezone-aware earnings date to naive date for matching
                e_date_naive = pd.Timestamp(edate).tz_localize(None).normalize()
                
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
                        
                    t_minus_1_price = history.iloc[t0_loc - 1]['Close']
                    t_0_price = history.iloc[t0_loc]['Close']
                    
                    # Ensure we have data for T+1 and T+14
                    if t0_loc + 1 >= len(history):
                        # Still drifting, T+1 hasn't finished
                        continue
                        
                    t_1_price = history.iloc[t0_loc + 1]['Close']
                    
                    # If T+14 doesn't exist yet, use the latest available price up to T+14
                    t_14_loc = min(t0_loc + 14, len(history) - 1)
                    t_14_price = history.iloc[t_14_loc]['Close']
                    
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
