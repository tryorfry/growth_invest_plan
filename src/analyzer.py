"""Stock analyzer using Facade pattern to coordinate data sources"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .data_sources.base import DataSource
from .data_sources.yfinance_source import YFinanceSource
from .data_sources.finviz_source import FinvizSource
from .data_sources.marketbeat_source import MarketBeatSource


@dataclass
class StockAnalysis:
    """Data class to hold complete stock analysis results"""
    
    ticker: str
    timestamp: Any = None
    
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
        analyst_source: Optional[DataSource] = None
    ):
        """
        Initialize the analyzer with data sources.
        
        Args:
            technical_source: Source for technical data (default: YFinance)
            fundamental_source: Source for fundamentals (default: Finviz)
            analyst_source: Source for analyst data (default: MarketBeat)
        """
        self.technical_source = technical_source or YFinanceSource()
        self.fundamental_source = fundamental_source or FinvizSource()
        self.analyst_source = analyst_source or MarketBeatSource()
    
    def analyze(self, ticker: str, verbose: bool = True) -> Optional[StockAnalysis]:
        """
        Perform complete stock analysis.
        
        Args:
            ticker: Stock ticker symbol
            verbose: Print progress messages
            
        Returns:
            StockAnalysis object with all collected data or None if failed
        """
        ticker = ticker.upper()
        analysis = StockAnalysis(ticker=ticker)
        
        # Fetch technical data
        if verbose:
            print(f"Fetching historical data for {ticker}...")
        
        technical_data = self.technical_source.fetch(ticker)
        if not technical_data:
            print(f"Error: No data found for ticker '{ticker}'")
            return None
        
        self._populate_technical_data(analysis, technical_data)
        
        # Fetch analyst targets (requires earnings date)
        if analysis.last_earnings_date and verbose:
            print(f"Fetching MarketBeat analyst ratings (post-earnings date: {analysis.last_earnings_date.date()})...")
        
        if analysis.last_earnings_date:
            analyst_data = self.analyst_source.fetch(
                ticker, 
                last_earnings_date=analysis.last_earnings_date
            )
            if analyst_data:
                analysis.median_price_target = analyst_data.get("median_price_target")
        
        # Fetch fundamental data
        if verbose:
            print("Fetching Finviz fundamental data...")
        
        fundamental_data = self.fundamental_source.fetch(ticker)
        if fundamental_data:
            analysis.finviz_data = fundamental_data
        
        return analysis
    
    def _populate_technical_data(self, analysis: StockAnalysis, data: Dict[str, Any]) -> None:
        """Populate analysis object with technical data"""
        analysis.current_price = data.get("current_price", 0.0)
        analysis.open = data.get("open", 0.0)
        analysis.high = data.get("high", 0.0)
        analysis.low = data.get("low", 0.0)
        analysis.close = data.get("close", 0.0)
        analysis.atr = data.get("atr", 0.0)
        analysis.ema20 = data.get("ema20", 0.0)
        analysis.ema50 = data.get("ema50", 0.0)
        analysis.ema200 = data.get("ema200", 0.0)
        analysis.timestamp = data.get("timestamp")
        
        # Earnings
        analysis.last_earnings_date = data.get("last_earnings_date")
        analysis.next_earnings_date = data.get("next_earnings_date")
        analysis.days_until_earnings = data.get("days_until_earnings")
        
        # Financials
        analysis.revenue = data.get("revenue")
        analysis.operating_income = data.get("operating_income")
        analysis.basic_eps = data.get("basic_eps")
