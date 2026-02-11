"""YFinance data source for technical and financial data"""

from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf
from datetime import datetime

from .base import TechnicalDataSource


class YFinanceSource(TechnicalDataSource):
    """Fetches technical indicators and financial data from Yahoo Finance"""
    
    def __init__(self, period: str = "2y"):
        """
        Initialize YFinance data source.
        
        Args:
            period: Historical data period (default: 2 years for EMA200)
        """
        self.period = period
    
    def get_source_name(self) -> str:
        return "YFinance"
    
    def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch technical and financial data from Yahoo Finance.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with technical indicators, financials, and earnings data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=self.period)
            
            if hist.empty:
                return None
            
            # Calculate technical indicators
            technical = self._calculate_technical_indicators(hist)
            
            # Get earnings dates
            earnings = self._get_earnings_dates(stock)
            
            # Get financial data
            financials = self._get_financial_data(stock)
            
            return {
                **technical,
                **earnings,
                **financials
            }
            
        except Exception as e:
            print(f"Error fetching YFinance data: {e}")
            return None
    
    def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate ATR and EMAs from historical data"""
        # True Range calculation
        high_low = hist['High'] - hist['Low']
        high_close = (hist['High'] - hist['Close'].shift()).abs()
        low_close = (hist['Low'] - hist['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # ATR (14-day)
        atr = true_range.ewm(span=14, adjust=False).mean()
        
        # EMAs
        ema20 = hist['Close'].ewm(span=20, adjust=False).mean()
        ema50 = hist['Close'].ewm(span=50, adjust=False).mean()
        ema200 = hist['Close'].ewm(span=200, adjust=False).mean()
        
        # Latest values
        latest = hist.iloc[-1]
        latest_date = hist.index[-1]
        
        return {
            "atr": atr.iloc[-1],
            "ema20": ema20.iloc[-1],
            "ema50": ema50.iloc[-1],
            "ema200": ema200.iloc[-1],
            "open": latest['Open'],
            "high": latest['High'],
            "low": latest['Low'],
            "close": latest['Close'],
            "current_price": latest['Close'],
            "timestamp": latest_date
        }
    
    def _get_earnings_dates(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Extract past and future earnings dates"""
        result = {}
        
        # Last earnings date
        earnings = stock.earnings_dates
        if earnings is not None and not earnings.empty:
            now = pd.Timestamp.now(tz=earnings.index.tz)
            past_earnings = earnings[earnings.index < now]
            if not past_earnings.empty:
                result["last_earnings_date"] = past_earnings.index[0]
        
        # Next earnings date
        next_earnings = None
        days_until = None
        
        # Try calendar first
        cal = stock.calendar
        if cal and "Earnings Date" in cal:
            dates = cal["Earnings Date"]
            if dates:
                next_earnings = dates[0]
        
        # Fallback to earnings_dates
        if not next_earnings and earnings is not None and not earnings.empty:
            now = pd.Timestamp.now(tz=earnings.index.tz)
            future = earnings[earnings.index > now].sort_index()
            if not future.empty:
                next_earnings = future.index[0]
        
        if next_earnings:
            # Handle timezone conversion
            if not isinstance(next_earnings, pd.Timestamp):
                next_earnings = pd.Timestamp(next_earnings)
            
            if next_earnings.tz:
                now = pd.Timestamp.now(tz=next_earnings.tz)
            else:
                now = pd.Timestamp.now()
            
            delta = next_earnings - now
            days_until = delta.days
            
            result["next_earnings_date"] = next_earnings
            result["days_until_earnings"] = days_until
        
        return result
    
    def _get_financial_data(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Extract quarterly financial data"""
        result = {}
        
        try:
            q_fin = stock.quarterly_financials
            if not q_fin.empty:
                latest_q = q_fin.iloc[:, 0]
                result["revenue"] = latest_q.get("Total Revenue", None)
                result["operating_income"] = latest_q.get("Operating Income", None)
                result["basic_eps"] = latest_q.get("Basic EPS", None)
        except Exception as e:
            print(f"Error fetching financials: {e}")
        
        return result
