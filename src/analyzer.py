"""Stock analyzer using Facade pattern to coordinate data sources"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from .data_sources.base import DataSource
from .data_sources.yfinance_source import YFinanceSource
from .data_sources.finviz_source import FinvizSource
from .data_sources.marketbeat_source import MarketBeatSource
from .data_sources.yfinance_analyst_source import YFinanceAnalystSource
from .data_sources.news_source import NewsSource


@dataclass
class StockAnalysis:
    """Data class to hold complete stock analysis results"""
    
    ticker: str
    timestamp: Any = None
    analysis_timestamp: Any = None  # Actual time of analysis
    
    # Company info
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Historical Data (for charts)
    history: Optional[pd.DataFrame] = None
    
    # Technical indicators
    current_price: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    atr: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    
    # Earnings
    last_earnings_date: Any = None
    next_earnings_date: Any = None
    days_until_earnings: Optional[int] = None
    
    # Financials
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    basic_eps: Optional[float] = None
    
    # Finviz fundamentals
    finviz_data: Dict[str, str] = field(default_factory=dict)
    
    # Analyst targets
    median_price_target: Optional[float] = None
    analyst_source: Optional[str] = None
    
    # Valuation data
    book_value: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    shares_outstanding: Optional[int] = None
    earnings_growth: Optional[float] = None
    
    # News Sentiment
    news_sentiment: Optional[float] = None
    news_summary: Optional[str] = None
    
    # Options data
    implied_volatility: Optional[float] = None
    put_call_ratio: Optional[float] = None
    
    # Insider trading
    insider_ownership_pct: Optional[float] = None
    net_insider_activity: Optional[float] = None
    
    # Short interest
    short_percent_of_float: Optional[float] = None
    short_ratio: Optional[float] = None  # Days to cover
    
    # Candlestick patterns
    recent_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Candlestick patterns
    recent_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Support & Resistance
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # Advanced Trade Setup
    market_trend: Optional[str] = "Sideways" # Uptrend, Downtrend, Sideways
    suggested_entry: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    
    def has_earnings_warning(self) -> bool:
        """Check if earnings are within 10 days"""
        return self.days_until_earnings is not None and self.days_until_earnings < 10


class StockAnalyzer:
    """
    Facade class that coordinates multiple data sources to analyze stocks.
    Uses Strategy pattern for pluggable data sources.
    """
    
    def __init__(
        self,
        technical_source: Optional[DataSource] = None,
        fundamental_source: Optional[DataSource] = None,
        analyst_source: Optional[DataSource] = None,
        news_source: Optional[DataSource] = None
    ):
        """
        Initialize the analyzer with data sources.
        
        Args:
            technical_source: Source for technical data (default: YFinance)
            fundamental_source: Source for fundamentals (default: Finviz)
            analyst_source: Source for analyst data (default: MarketBeat)
            news_source: Source for sentiment (default: NewsSource)
        """
        self.technical_source = technical_source or YFinanceSource()
        self.fundamental_source = fundamental_source or FinvizSource()
        self.analyst_source = analyst_source or MarketBeatSource()
        self.news_source = news_source or NewsSource()
    
    async def analyze(self, ticker: str, verbose: bool = True) -> Optional[StockAnalysis]:
        """
        Perform complete stock analysis asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            verbose: Print progress messages
            
        Returns:
            StockAnalysis object with all collected data or None if failed
        """
        import asyncio
        
        ticker = ticker.upper()
        analysis = StockAnalysis(
            ticker=ticker,
            analysis_timestamp=datetime.now()
        )
        
        if verbose:
            print(f"Fetching data for {ticker}...")
            
        # 1. Fetch Technical, Fundamental, and News data in parallel
        # We need technical data first for earnings date, but Finviz/News are independent
        technical_task = asyncio.create_task(self.technical_source.fetch(ticker))
        fundamental_task = asyncio.create_task(self.fundamental_source.fetch(ticker))
        news_task = asyncio.create_task(self.news_source.fetch(ticker))
        
        results = await asyncio.gather(technical_task, fundamental_task, news_task)
        technical_data, fundamental_data, news_data = results
        
        if not technical_data:
            print(f"Error: No technical data found for ticker '{ticker}'")
            return None
            
        self._populate_technical_data(analysis, technical_data)
        
        if fundamental_data:
            analysis.finviz_data = fundamental_data
            
        if news_data:
            analysis.news_sentiment = news_data.get("news_sentiment")
            analysis.news_summary = news_data.get("news_summary")
            
        if news_data:
            analysis.news_sentiment = news_data.get("news_sentiment")
            analysis.news_summary = news_data.get("news_summary")
            
        # Calculate Support & Resistance if history exists
        if analysis.history is not None and not analysis.history.empty:
            self._calculate_support_resistance(analysis)
            self._calculate_trade_setup(analysis)
            
        # 2. Fetch Analyst Targets (Dependent on earnings date from technical data)
        if analysis.last_earnings_date:
            analyst_data = None
            
            # Try primary analyst source (default: MarketBeat)
            if verbose:
                print(f"Fetching analyst ratings (post {analysis.last_earnings_date.date()}) from {self.analyst_source.get_source_name()}...")
                
            analyst_data = await self.analyst_source.fetch(
                ticker, 
                last_earnings_date=analysis.last_earnings_date
            )
            
            if analyst_data:
                analysis.median_price_target = analyst_data.get("median_price_target")
                analysis.analyst_source = self.analyst_source.get_source_name()
            else:
                # Fallback to YFinance if primary fails and isn't already YFinance
                if not isinstance(self.analyst_source, YFinanceAnalystSource):
                    if verbose:
                        print(f"Primary analyst source failed, falling back to YFinance...")
                    
                    yf_source = YFinanceAnalystSource()
                    analyst_data = await yf_source.fetch(
                        ticker,
                        last_earnings_date=analysis.last_earnings_date
                    )
                    if analyst_data:
                        analysis.median_price_target = analyst_data.get("median_price_target")
                        analysis.analyst_source = "YFinance (Fallback)"
        
        return analysis
    
    def _populate_technical_data(self, analysis: StockAnalysis, data: Dict[str, Any]) -> None:
        """Populate analysis object with technical data"""
        analysis.history = data.get("history")
        analysis.current_price = data.get("current_price", 0.0)
        analysis.open = data.get("open", 0.0)
        analysis.high = data.get("high", 0.0)
        analysis.low = data.get("low", 0.0)
        analysis.close = data.get("close", 0.0)
        analysis.atr = data.get("atr", 0.0)
        analysis.ema20 = data.get("ema20", 0.0)
        analysis.ema50 = data.get("ema50", 0.0)
        analysis.ema200 = data.get("ema200", 0.0)
        analysis.rsi = data.get("rsi", 0.0)
        analysis.macd = data.get("macd", 0.0)
        analysis.macd_signal = data.get("macd_signal", 0.0)
        analysis.bollinger_upper = data.get("bollinger_upper", 0.0)
        analysis.bollinger_lower = data.get("bollinger_lower", 0.0)
        analysis.timestamp = data.get("timestamp")
        
        # Earnings
        analysis.last_earnings_date = data.get("last_earnings_date")
        analysis.next_earnings_date = data.get("next_earnings_date")
        analysis.days_until_earnings = data.get("days_until_earnings")
        
        # Financials
        analysis.revenue = data.get("revenue")
        analysis.operating_income = data.get("operating_income")
        analysis.basic_eps = data.get("basic_eps")
        
        # Company info
        analysis.company_name = data.get("company_name")
        analysis.sector = data.get("sector")
        analysis.industry = data.get("industry")
        
        # Valuation data
        analysis.book_value = data.get("book_value")
        analysis.free_cash_flow = data.get("free_cash_flow")
        analysis.total_debt = data.get("total_debt")
        analysis.total_cash = data.get("total_cash")
        analysis.shares_outstanding = data.get("shares_outstanding")
        analysis.earnings_growth = data.get("earnings_growth")

    def _calculate_support_resistance(self, analysis: StockAnalysis) -> None:
        """
        Calculate major support and resistance levels using local extrema.
        Simple logic: Find local mins/maxs over a 20-day window.
        """
        df = analysis.history
        if df is None or len(df) < 20:
            return
            
        # Use a rolling window to find local min/max
        # Simulating "fractals" - a high surrounded by lower highs, etc.
        # But simpler: use scipy.signal.argrelextrema-like logic manually or simple window
        
        # We'll just define support as local min in 5-day window, resistance as max
        # Then we cluster them.
        
        levels = []
        for i in range(2, len(df) - 2):
            # 5-bar fractal check
            # High
            if (df['High'].iloc[i] > df['High'].iloc[i-1] and 
                df['High'].iloc[i] > df['High'].iloc[i-2] and 
                df['High'].iloc[i] > df['High'].iloc[i+1] and 
                df['High'].iloc[i] > df['High'].iloc[i+2]):
                levels.append((df['High'].iloc[i], 'resistance'))
                
            # Low
            if (df['Low'].iloc[i] < df['Low'].iloc[i-1] and 
                df['Low'].iloc[i] < df['Low'].iloc[i-2] and 
                df['Low'].iloc[i] < df['Low'].iloc[i+1] and 
                df['Low'].iloc[i] < df['Low'].iloc[i+2]):
                levels.append((df['Low'].iloc[i], 'support'))
        
        # Now cluster close levels together
        # Sort levels by price
        # Filter to keep only the most significant (e.g. recently touched or multiple touches)
        # This is a simplified version: just take the most recent 3 distinct levels above/below current price
        
        current_price = analysis.current_price
        
        supports = sorted([l[0] for l in levels if l[1] == 'support' and l[0] < current_price])
        resistances = sorted([l[0] for l in levels if l[1] == 'resistance' and l[0] > current_price])
        
        # Simple Clustering: If levels are within 2%, keep only the most recent (effectively assumed via list order, but better to group)
        # For simplicity in this v1, just take the top 3 nearest supports and resistances
        
        # Nearest supports (highest values below price)
        if supports:
            # Filter close values
            unique_supports = []
            if supports:
                unique_supports.append(supports[-1]) # Closest support
                for s in reversed(supports[:-1]):
                    if abs(s - unique_supports[-1]) / unique_supports[-1] > 0.02: # 2% gap
                        unique_supports.append(s)
            analysis.support_levels = unique_supports[:3] # Keep top 3 nearest
            
        # Nearest resistances (lowest values above price)
        if resistances:
            # Filter close values
            unique_resistances = []
            if resistances:
                unique_resistances.append(resistances[0]) # Closest resistance
                for r in resistances[1:]:
                    if abs(r - unique_resistances[-1]) / unique_resistances[-1] > 0.02:
                        unique_resistances.append(r)
            analysis.resistance_levels = unique_resistances[:3] # Keep top 3 nearest

    def _calculate_trade_setup(self, analysis: StockAnalysis) -> None:
        """
        Determine market trend and calculate smart entry/exit points.
        Trend Logic:
            - Uptrend: Price > EMA50 > EMA200
            - Downtrend: Price < EMA50 < EMA200
            - Sideways: Everything else
            
        Entry Logic:
            - 0.2% to 1.0% above nearest support.
            - Round to "odd" decimals (.13, .17, .77) to avoiding piling with the crowd.
            - Formula: Support * (1 + 0.005) -> Round logic
            
        Stop Loss:
            - Support - 1.0 * ATR
        """
        # 1. Determine Trend
        price = analysis.current_price
        ema50 = analysis.ema50
        ema200 = analysis.ema200
        
        if price > ema50 and ema50 > ema200:
            analysis.market_trend = "Uptrend"
        elif price < ema50 and ema50 < ema200:
            analysis.market_trend = "Downtrend"
        else:
            analysis.market_trend = "Sideways"
            
        # 2. Find nearest support level below current price
        valid_supports = [s for s in analysis.support_levels if s < price]
        nearest_support = valid_supports[-1] if valid_supports else None
        
        if nearest_support and analysis.atr > 0:
            # Entry Calculation (0.5% buffer above support)
            raw_entry = nearest_support * 1.005
            analysis.suggested_entry = self._apply_smart_rounding(raw_entry)
            
            # Stop Loss Calculation (Support - 1 ATR)
            raw_stop = nearest_support - analysis.atr
            analysis.suggested_stop_loss = round(raw_stop, 2)
            
    def _apply_smart_rounding(self, price: float) -> float:
        """
        Round price to specific 'odd' decimals (.13, .17, .37, .77) 
        to avoid round number clustering (.00, .10, .50).
        """
        # Get the integer part and the decimal part
        integer_part = int(price)
        decimal_part = price - integer_part
        
        # Define target endings
        targets = [0.13, 0.17, 0.37, 0.43, 0.77, 0.83, 0.97]
        
        # Find closest target
        best_target = targets[0]
        min_diff = abs(decimal_part - targets[0])
        
        for t in targets:
            diff = abs(decimal_part - t)
            if diff < min_diff:
                min_diff = diff
                best_target = t
                
        return integer_part + best_target
