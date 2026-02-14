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
