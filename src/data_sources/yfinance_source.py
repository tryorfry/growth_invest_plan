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
    
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch technical and financial data from Yahoo Finance asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with technical indicators, financials, and earnings data
        """
        import asyncio
        loop = asyncio.get_running_loop()
        
        # Run blocking yfinance calls in a thread pool
        return await loop.run_in_executor(None, self._fetch_sync, ticker)

    def _fetch_sync(self, ticker: str) -> Optional[Dict[str, Any]]:
        # Synchronous fetch logic for thread execution
        # Let exceptions bubble up to be handled by the caller or UI
        stock = yf.Ticker(ticker)
        hist = stock.history(period=self.period)
        
        if hist.empty:
            raise ValueError(f"No price data found for {ticker}")
        
        # Calculate technical indicators
        technical = self._calculate_technical_indicators(hist)
        
        # Get earnings dates
        try:
            earnings = self._get_earnings_dates(stock)
        except Exception as e:
            print(f"Error fetching earnings dates: {e}")
            earnings = {}
        
        # Get financial data
        financials = self._get_financial_data(stock)
        
        # Get company info
        company_info = self._get_company_info(stock)
        
        # Get Insider Transaction dates
        insider_dates = {"insider_buy_dates": [], "insider_sell_dates": []}
        try:
            txns = stock.insider_transactions
            if txns is not None and not txns.empty:
                for _, row in txns.head(50).iterrows():
                    start_date = row.get('Start Date')
                    if pd.notna(start_date):
                        date_str = start_date.strftime('%Y-%m-%d')
                        txn_raw = str(row.get('Transaction', '')).lower()
                        if 'purchase' in txn_raw or 'buy' in txn_raw:
                            insider_dates["insider_buy_dates"].append(date_str)
                        elif 'sale' in txn_raw or 'sell' in txn_raw:
                            insider_dates["insider_sell_dates"].append(date_str)
        except Exception as e:
            print(f"Error fetching insider dates: {e}")
            
        return {
            **technical,
            **earnings,
            **financials,
            **company_info,
            **insider_dates
        }
    
    def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate ATR, EMAs, RSI, MACD, and Bollinger Bands from historical data"""
        # Calculate True Range (TR) & ATR
        high_low = hist['High'] - hist['Low']
        high_close = (hist['High'] - hist['Close'].shift()).abs()
        low_close = (hist['Low'] - hist['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # ATR 14 - using Wilder's Smoothing (com = period - 1, so alpha = 1/period)
        atr = true_range.ewm(com=13, adjust=False).mean()
        hist['ATR'] = atr
        
        # EMAs
        ema20 = hist['Close'].ewm(span=20, adjust=False).mean()
        ema50 = hist['Close'].ewm(span=50, adjust=False).mean()
        ema200 = hist['Close'].ewm(span=200, adjust=False).mean()
        
        hist['EMA20'] = ema20
        hist['EMA50'] = ema50
        hist['EMA200'] = ema200
        
        # RSI (Relative Strength Index) - 14 period
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        hist['RSI'] = rsi
        
        # MACD (Moving Average Convergence Divergence)
        ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        hist['MACD'] = macd
        hist['MACD_Signal'] = macd_signal
        
        # Bollinger Bands (20 period, 2 std dev)
        sma20 = hist['Close'].rolling(window=20).mean()
        std20 = hist['Close'].rolling(window=20).std()
        bollinger_upper = sma20 + (std20 * 2)
        bollinger_lower = sma20 - (std20 * 2)
        hist['Bollinger_Upper'] = bollinger_upper
        hist['Bollinger_Lower'] = bollinger_lower
        
        # Latest values
        latest = hist.iloc[-1]
        latest_date = hist.index[-1]
        
        # Dividends
        dividend_dates = hist[hist['Dividends'] > 0].index.strftime('%Y-%m-%d').tolist() if 'Dividends' in hist.columns else []

        return {
            "dividend_dates": dividend_dates,
            "history": hist,
            "atr": atr.iloc[-1],
            "ema20": ema20.iloc[-1],
            "ema50": ema50.iloc[-1],
            "ema200": ema200.iloc[-1],
            "rsi": rsi.iloc[-1],
            "macd": macd.iloc[-1],
            "macd_signal": macd_signal.iloc[-1],
            "bollinger_upper": bollinger_upper.iloc[-1],
            "bollinger_lower": bollinger_lower.iloc[-1],
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
        
        # Last earnings date and all past dates
        earnings = stock.earnings_dates
        if earnings is not None and not earnings.empty:
            now = pd.Timestamp.now(tz=earnings.index.tz)
            past_earnings = earnings[earnings.index < now]
            if not past_earnings.empty:
                result["last_earnings_date"] = past_earnings.index[0]
                result["past_earnings_dates"] = past_earnings.index.tolist()
        
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
                
                # YoY growth (needs at least 5 quarters to compare latest with 1 year ago)
                if q_fin.shape[1] >= 5:
                    yoy_q = q_fin.iloc[:, 4]
                    
                    rev_now = latest_q.get("Total Revenue")
                    rev_yoy = yoy_q.get("Total Revenue")
                    if rev_now is not None and rev_yoy is not None and rev_yoy != 0:
                        result["revenue_growth_yoy"] = (rev_now - rev_yoy) / abs(rev_yoy)
                        
                    op_now = latest_q.get("Operating Income")
                    op_yoy = yoy_q.get("Operating Income")
                    if op_now is not None and op_yoy is not None and op_yoy != 0:
                        result["op_income_growth_yoy"] = (op_now - op_yoy) / abs(op_yoy)
                        
                    eps_now = latest_q.get("Basic EPS")
                    eps_yoy = yoy_q.get("Basic EPS")
                    if eps_now is not None and eps_yoy is not None and eps_yoy != 0:
                        result["eps_growth_yoy"] = (eps_now - eps_yoy) / abs(eps_yoy)
        except Exception as e:
            print(f"Error fetching financials: {e}")
        
        return result
    
    def _get_company_info(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Extract company sector and industry information"""
        result = {}
        
        try:
            info = stock.info
            if info:
                result["sector"] = info.get("sector", None)
                result["industry"] = info.get("industry", None)
                result["company_name"] = info.get("longName", None)
                
                # Checklist fields
                result["country"] = info.get("country", None)
                result["exchange"] = info.get("exchange", None)  # e.g. NMS, NYQ, NGM, PCX
                result["average_volume"] = info.get("averageVolume", None)
                result["analyst_recommendation"] = info.get("recommendationKey", None)
                
                # Valuation fields
                result["book_value"] = info.get("bookValue")
                result["free_cash_flow"] = info.get("freeCashflow")
                result["total_debt"] = info.get("totalDebt")
                result["total_cash"] = info.get("totalCash")
                result["shares_outstanding"] = info.get("sharesOutstanding")
                result["earnings_growth"] = info.get("earningsGrowth")
        except Exception as e:
            print(f"Error fetching company info: {e}")
        
        return result
