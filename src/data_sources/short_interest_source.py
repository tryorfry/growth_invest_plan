"""Short interest data source"""

import yfinance as yf
from typing import Dict, Any
from datetime import datetime


class ShortInterestSource:
    """Fetch short interest metrics"""
    
    def fetch_short_interest(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch short interest data for a stock.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with short interest metrics
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get short interest metrics
            short_percent = info.get('shortPercentOfFloat', 0) * 100 if info.get('shortPercentOfFloat') else 0
            short_ratio = info.get('shortRatio', 0)
            shares_short = info.get('sharesShort', 0)
            shares_short_prior = info.get('sharesShortPriorMonth', 0)
            
            # Calculate change in short interest
            short_change = 0
            if shares_short_prior > 0:
                short_change = ((shares_short - shares_short_prior) / shares_short_prior) * 100
            
            return {
                'short_percent_of_float': short_percent,
                'short_ratio': short_ratio,  # Days to cover
                'shares_short': shares_short,
                'shares_short_prior_month': shares_short_prior,
                'short_interest_change_pct': short_change,
                'fetched_at': datetime.now()
            }
            
        except Exception as e:
            print(f"Error fetching short interest for {ticker}: {e}")
            return {
                'short_percent_of_float': 0,
                'short_ratio': 0,
                'error': str(e)
            }
