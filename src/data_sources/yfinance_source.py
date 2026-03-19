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
        
        try:
            hist = stock.history(period=self.period)
            if hist.empty:
                raise ValueError("hist is empty")
        except Exception as e:
            # Fallback direct request if yfinance fails to parse (NoneType bug)
            print(f"yfinance failed, attempting direct fetch for {ticker}: {e}")
            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            })
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={self.period}&interval=1d"
            r = session.get(url)
            data = r.json()
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quote = result['indicators']['quote'][0]
                hist = pd.DataFrame({
                    'Open': quote['open'],
                    'High': quote['high'],
                    'Low': quote['low'],
                    'Close': quote['close'],
                    'Volume': quote['volume']
                }, index=pd.to_datetime(timestamps, unit='s', utc=True))
                # yfinance returns timezone-aware localized series, so we convert back to simple naive dates based on market tz
                hist.index = hist.index.tz_convert('America/New_York')
            else:
                hist = pd.DataFrame()
        
        if hist.empty:
            raise ValueError(f"No price data found for {ticker}")
            
        # LIVE PRICE INJECTION:
        # yfinance daily history often lacks the *current* intraday price during market hours
        # or caches heavily. We fetch the live quote and update the last row if it's today.
        try:
            # fast_info is much faster than info dict
            live_price = stock.fast_info.get("lastPrice")
            if live_price is not None:
                now_tz = pd.Timestamp.now(tz=hist.index.tz) if hist.index.tz else pd.Timestamp.now()
                # Check if the last row in history is from today
                last_date = hist.index[-1]
                
                if last_date.date() == now_tz.date():
                    # Update today's existing row
                    hist.loc[last_date, 'Close'] = live_price
                    hist.loc[last_date, 'High'] = max(hist.loc[last_date, 'High'], live_price)
                    hist.loc[last_date, 'Low'] = min(hist.loc[last_date, 'Low'], live_price)
                else:
                    # Append a new row for today
                    new_row = pd.DataFrame({
                        'Open': [live_price],
                        'High': [live_price],
                        'Low': [live_price],
                        'Close': [live_price],
                        'Volume': [0]  # We don't have accurate live daily volume here easily, but price is key
                    }, index=[now_tz])
                    hist = pd.concat([hist, new_row])
        except Exception as e:
            print(f"Warning: Failed to fetch/inject live price for {ticker}: {e}")
            
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
        
        # Weekly ATR 14w - using Wilder's Smoothing on weekly data
        weekly_hist = hist.resample('W-FRI').agg({
            'High': 'max',
            'Low': 'min',
            'Close': 'last'
        }).dropna()
        
        whigh_low = weekly_hist['High'] - weekly_hist['Low']
        whigh_close = (weekly_hist['High'] - weekly_hist['Close'].shift()).abs()
        wlow_close = (weekly_hist['Low'] - weekly_hist['Close'].shift()).abs()
        wtrue_range = pd.concat([whigh_low, whigh_close, wlow_close], axis=1).max(axis=1)
        
        # Use Wilder's Smoothing (RMA) for ATR to match industry standards
        watr = wtrue_range.ewm(alpha=1/14, adjust=False).mean()
        
        # Broadcast weekly ATR back to daily indices via forward fill
        atr = watr.reindex(hist.index, method='ffill')
        hist['ATR'] = atr
        
        # Daily ATR 14d - using Wilder's Smoothing on daily data for Swing Trading
        datr = true_range.ewm(alpha=1/14, adjust=False).mean()
        hist['ATR_Daily'] = datr
        
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
        
        # ── Trend Channel (Dynamic window, parallel High/Low regression bands) ──
        # 1. Detect the natural swing cycle from the PatternRecognition engine
        #    to decide how wide the regression window should be.
        import numpy as np
        try:
            from src.pattern_recognition import PatternRecognition
            _pr = PatternRecognition()
            _hl = _pr.detect_relative_high_low(hist)
            _pivots = _hl.get('pivots', [])
            if len(_pivots) >= 3:
                # Compute average bar-distance between consecutive pivots as cycle length
                pivot_idx = [p['index'] for p in _pivots[-8:] if 'index' in p]
                if len(pivot_idx) >= 2:
                    gaps = [abs(pivot_idx[i+1] - pivot_idx[i]) for i in range(len(pivot_idx)-1)]
                    avg_gap = int(np.mean(gaps))
                    # Use 2 full cycles as window; clamp between 30 and 90 days
                    reg_window = max(30, min(90, avg_gap * 2))
                else:
                    reg_window = 50
            else:
                reg_window = 50
        except Exception:
            reg_window = 50

        def calc_lin_reg_endpoint(close_vals):
            """Returns the predicted Close value at the last point of the window."""
            if len(close_vals) < reg_window: return np.nan
            x = np.arange(len(close_vals))
            coef = np.polyfit(x, close_vals, 1)
            return coef[0] * (len(close_vals) - 1) + coef[1]

        hist['Trend_Center'] = hist['Close'].rolling(window=reg_window, min_periods=reg_window).apply(
            calc_lin_reg_endpoint, raw=True
        )

        # 2. Parallel bands: offset by max(High-predicted) / min(Low-predicted) within window
        close_arr = hist['Close'].values
        high_arr  = hist['High'].values
        low_arr   = hist['Low'].values
        n = len(hist)
        upper_offset = np.full(n, np.nan)
        lower_offset = np.full(n, np.nan)
        channel_slope = np.full(n, np.nan)

        for i in range(reg_window - 1, n):
            wc = close_arr[i - reg_window + 1: i + 1]
            wh = high_arr[i - reg_window + 1: i + 1]
            wl = low_arr[i - reg_window + 1: i + 1]
            if np.any(np.isnan(wc)): continue
            x = np.arange(reg_window)
            coef = np.polyfit(x, wc, 1)
            predicted = coef[0] * x + coef[1]
            upper_offset[i] = np.max(wh - predicted)
            lower_offset[i] = np.min(wl - predicted)
            channel_slope[i] = coef[0]   # raw slope ($/bar)

        hist['Trend_Upper'] = hist['Trend_Center'] + pd.Series(upper_offset, index=hist.index)
        hist['Trend_Lower'] = hist['Trend_Center'] + pd.Series(lower_offset, index=hist.index)
        hist['Channel_Slope'] = pd.Series(channel_slope, index=hist.index)

        # 3. Channel direction classification (normalised by price level)
        last_slope = channel_slope[~np.isnan(channel_slope)][-1] if np.any(~np.isnan(channel_slope)) else 0.0
        last_close = hist['Close'].iloc[-1]
        # Express slope as % of price per bar — threshold ±0.05% per day
        slope_pct = (last_slope / last_close) * 100 if last_close > 0 else 0
        if slope_pct > 0.05:
            channel_direction = "Rising"
        elif slope_pct < -0.05:
            channel_direction = "Falling"
        else:
            channel_direction = "Flat"

        # 4. Weekly EMAs from daily data for multi-timeframe confirmation (#8)
        weekly_hist = hist.resample('W-FRI').agg({'Close': 'last'}).dropna()
        w_ema20 = weekly_hist['Close'].ewm(span=20, adjust=False).mean().iloc[-1] if len(weekly_hist) >= 20 else None
        w_ema50 = weekly_hist['Close'].ewm(span=50, adjust=False).mean().iloc[-1] if len(weekly_hist) >= 50 else None

        
        # Latest values
        latest = hist.iloc[-1]
        latest_date = hist.index[-1]
        
        # Dividends
        dividend_dates = hist[hist['Dividends'] > 0].index.strftime('%Y-%m-%d').tolist() if 'Dividends' in hist.columns else []

        return {
            "dividend_dates": dividend_dates,
            "history": hist,
            "atr": atr.iloc[-1],
            "atr_daily": datr.iloc[-1] if 'ATR_Daily' in hist else 0.0,
            "ema20": ema20.iloc[-1],
            "ema50": ema50.iloc[-1],
            "ema200": ema200.iloc[-1],
            "rsi": rsi.iloc[-1],
            "macd": macd.iloc[-1],
            "macd_signal": macd_signal.iloc[-1],
            "bollinger_upper": bollinger_upper.iloc[-1],
            "bollinger_lower": bollinger_lower.iloc[-1],
            "channel_direction": channel_direction,
            "weekly_ema20": w_ema20,
            "weekly_ema50": w_ema50,
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
