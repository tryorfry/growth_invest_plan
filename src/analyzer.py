"""Stock analyzer using Facade pattern to coordinate data sources"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from .data_sources.base import DataSource
from .data_sources.yfinance_source import YFinanceSource
from .data_sources.yfinance_analyst_source import YFinanceAnalystSource
from .data_sources.finviz_source import FinvizSource
from .data_sources.marketbeat_source import MarketBeatSource
from .data_sources.news_source import NewsSentimentSource
from .data_sources.macro_source import MacroSource
from .data_sources.macrotrends_source import MacrotrendsSource
from .trading_styles.factory import get_trading_style


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
    quoteType: Optional[str] = None
    
    # Historical Data (for charts)
    history: Optional[pd.DataFrame] = None
    
    # Technical indicators
    current_price: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    atr: float = 0.0
    atr_daily: float = 0.0  # Used for Swing Trading
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
    past_earnings_dates: List[Any] = field(default_factory=list)
    next_earnings_date: Any = None
    days_until_earnings: Optional[int] = None
    
    # Dividends & Insiders
    dividend_dates: List[str] = field(default_factory=list)
    insider_buy_dates: List[str] = field(default_factory=list)
    insider_sell_dates: List[str] = field(default_factory=list)
    
    # Financials
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    basic_eps: Optional[float] = None
    
    # Finviz fundamentals
    finviz_data: Dict[str, str] = field(default_factory=dict)
    
    # Checklist fields
    country: Optional[str] = None
    exchange: Optional[str] = None  # yfinance exchange code e.g. NMS, NYQ, NGM
    average_volume: Optional[int] = None
    analyst_recommendation: Optional[str] = None
    revenue_growth_yoy: Optional[float] = None
    op_income_growth_yoy: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    marketbeat_action_recent: Optional[str] = None
    max_buy_price: Optional[float] = None
    
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
    
    # Volume Profile
    volume_profile_hvns: List[float] = field(default_factory=list)
    volume_profile_lvns: List[float] = field(default_factory=list)
    
    # Support & Resistance
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # Advanced Trade Setup
    trading_style: str = "Growth Investing"
    market_trend: Optional[str] = "Sideways" # Uptrend, Downtrend, Sideways
    suggested_entry: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    reward_to_risk: Optional[float] = None
    risk_per_unit: Optional[float] = None
    position_size_units: Optional[int] = None
    setup_notes: List[str] = field(default_factory=list)
    swing_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Multi-Style Results
    style_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    style_analyses: Dict[str, Any] = field(default_factory=dict) # Full StockAnalysis objects for each style
    best_style: Optional[str] = None
    
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
        news_source: Optional[DataSource] = None,
        macrotrends_source: Optional[DataSource] = None
    ):
        """
        Initialize the analyzer with data sources.
        
        Args:
            technical_source: Source for technical data (default: YFinance)
            fundamental_source: Source for fundamentals (default: Finviz)
            analyst_source: Source for analyst data (default: MarketBeat)
            news_source: Source for sentiment (default: NewsSentimentSource)
            
        Returns:
            StockAnalyzer instance
        """
        self.technical_source = technical_source or YFinanceSource()
        self.fundamental_source = fundamental_source or FinvizSource()
        self.analyst_source = analyst_source or MarketBeatSource()
        self.news_source = news_source or NewsSentimentSource()
        self.macrotrends_source = macrotrends_source or MacrotrendsSource()
    
    async def analyze(self, ticker: str, trading_style_name: str = "Growth Investing", verbose: bool = True) -> Optional[StockAnalysis]:
        """
        Perform complete stock analysis asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            trading_style_name: Trading style (e.g. "Growth Investing" or "Swing Trading")
            verbose: Print progress messages
            
        Returns:
            StockAnalysis object with all collected data or None if failed
        """
        # Get historical data (usually 5 years weekly for Growth, Daily for Swing/Trend)
        # Note: Swing and Trend strategies need daily data for patterns/defaults
        interval = "1d" if trading_style_name in ["Swing Trading", "Trend Trading"] else "1wk"
        period = "2y" if trading_style_name in ["Swing Trading", "Trend Trading"] else "5y"
        import asyncio
        
        style_strategy = get_trading_style(trading_style_name)
        
        ticker = ticker.upper()
        analysis = StockAnalysis(
            ticker=ticker,
            trading_style=style_strategy.style_name,
            analysis_timestamp=datetime.now()
        )
        
        if verbose:
            print(f"Fetching data for {ticker}...")
            
        # 1. Fetch Technical, Fundamental, and News data in parallel
        # We need technical data first for earnings date, but Finviz/News are independent
        technical_task = asyncio.create_task(self.technical_source.fetch(ticker, interval=interval, period=period))
        fundamental_task = asyncio.create_task(self.fundamental_source.fetch(ticker))
        news_task = asyncio.create_task(self.news_source.fetch(ticker))
        macrotrends_task = asyncio.create_task(self.macrotrends_source.fetch(ticker))
        
        # Allow individual tasks to fail without cancelling others
        results = await asyncio.gather(technical_task, fundamental_task, news_task, macrotrends_task, return_exceptions=True)
        technical_data, fundamental_data, news_data, macrotrends_data = results
        
        # Check for critical technical data failure
        if isinstance(technical_data, Exception):
            print(f"Critical Error: Technical data fetch failed: {technical_data}")
            return None
            
        if not technical_data:
            print(f"Error: No technical data found for ticker '{ticker}'")
            return None
            
        self._populate_technical_data(analysis, technical_data)
        
        # Handle non-critical failures
        if isinstance(fundamental_data, Exception):
            print(f"Warning: Fundamental data fetch failed: {fundamental_data}")
            fundamental_data = {}
            
        if fundamental_data:
            analysis.finviz_data = fundamental_data
            
        if isinstance(news_data, Exception):
            print(f"Warning: News fetch failed: {news_data}")
            news_data = {}
            
        if news_data:
            analysis.news_sentiment = news_data.get("news_sentiment")
            analysis.news_summary = news_data.get("news_summary")
            
        # 2. Process Macrotrends data (Primary for core financials)
        if isinstance(macrotrends_data, Exception):
            print(f"Warning: Macrotrends fetch failed: {macrotrends_data}")
            macrotrends_data = None
            
        if macrotrends_data:
            # Override with Macrotrends data if available
            analysis.revenue = macrotrends_data.get('revenue', analysis.revenue)
            analysis.operating_income = macrotrends_data.get('operating_income', analysis.operating_income)
            analysis.basic_eps = macrotrends_data.get('eps_diluted', analysis.basic_eps)
            if verbose:
                print(f"Using Macrotrends for core financials.")
            
        # Calculate Support & Resistance if history exists
        if analysis.history is not None and not analysis.history.empty:
            self._calculate_support_resistance(analysis)
            # Execute Strategy Pattern Trade Setup
            style_strategy.calculate_trade_setup(analysis)
            
            if analysis.suggested_entry and analysis.suggested_stop_loss:
                risk = float(analysis.suggested_entry) - float(analysis.suggested_stop_loss)
                if risk > 0:
                    analysis.risk_per_unit = risk
                    analysis.position_size_units = int(100.0 // risk)
            
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
                analysis.marketbeat_action_recent = analyst_data.get("recent_action")
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
                        analysis.marketbeat_action_recent = analyst_data.get("recent_action")
                        analysis.analyst_source = "YFinance (Fallback)"
                        
        if analysis.median_price_target:
            analysis.max_buy_price = analysis.median_price_target / 1.15
        
        return analysis

    async def multi_analyze(self, ticker: str, verbose: bool = True) -> Optional[StockAnalysis]:
        """
        Runs all available trading styles for a ticker and finds the best one.
        Optimized by fetching data in parallel and reusing sources.
        """
        ticker = ticker.upper()
        import asyncio
        from .trading_styles.factory import get_trading_style
        
        try:
            # 1. Fetch all data needed for ALL styles in parallel
            # Growth needs W/5y, Swing/Trend need D/2y
            if verbose:
                print(f"Starting Multi-Style Analysis for {ticker}...")
                
            # Data fetching tasks
            weekly_task = asyncio.create_task(self.technical_source.fetch(ticker, interval="1wk", period="5y"))
            daily_task = asyncio.create_task(self.technical_source.fetch(ticker, interval="1d", period="2y"))
            fundamental_task = asyncio.create_task(self.fundamental_source.fetch(ticker))
            news_task = asyncio.create_task(self.news_source.fetch(ticker))
            macrotrends_task = asyncio.create_task(self.macrotrends_source.fetch(ticker))
            
            results = await asyncio.gather(weekly_task, daily_task, fundamental_task, news_task, macrotrends_task, return_exceptions=True)
            tech_w, tech_d, fundamental_data, news_data, macrotrends_data = results
            
            if isinstance(tech_d, Exception) or not tech_d:
                print(f"Error: Could not fetch basic technical data for {ticker}")
                return None

            # Base analysis object (using daily as default history)
            main_analysis = StockAnalysis(ticker=ticker, analysis_timestamp=datetime.now())
            self._populate_technical_data(main_analysis, tech_d)
            
            # Add fundamental/news data once
            if not isinstance(fundamental_data, Exception) and fundamental_data:
                main_analysis.finviz_data = fundamental_data
            if not isinstance(news_data, Exception) and news_data:
                main_analysis.news_sentiment = news_data.get("news_sentiment")
                main_analysis.news_summary = news_data.get("news_summary")
            if not isinstance(macrotrends_data, Exception) and macrotrends_data:
                main_analysis.revenue = macrotrends_data.get('revenue', main_analysis.revenue)
                main_analysis.operating_income = macrotrends_data.get('operating_income', main_analysis.operating_income)
                main_analysis.basic_eps = macrotrends_data.get('eps_diluted', main_analysis.basic_eps)

            # Analyst data (usually same for all)
            if main_analysis.last_earnings_date:
                analyst_data = await self.analyst_source.fetch(ticker, last_earnings_date=main_analysis.last_earnings_date)
                if analyst_data:
                    main_analysis.median_price_target = analyst_data.get("median_price_target")
                    main_analysis.marketbeat_action_recent = analyst_data.get("recent_action")
                    main_analysis.analyst_source = self.analyst_source.get_source_name()
            
            if main_analysis.median_price_target:
                main_analysis.max_buy_price = main_analysis.median_price_target / 1.15

            # 2. Run each style
            styles = ["Growth Investing", "Swing Trading", "Trend Trading"]
            style_scores = {}
            
            for style_name in styles:
                # Create a clone for each style to avoid interference
                import copy
                style_analysis = copy.copy(main_analysis)
                
                # Explicitly reset mutable state or create shallow copies of nested collections
                style_analysis.setup_notes = []
                style_analysis.support_levels = []
                style_analysis.resistance_levels = []
                style_analysis.swing_patterns = []
                style_analysis.volume_profile_hvns = []
                style_analysis.volume_profile_lvns = []
                style_analysis.finviz_data = main_analysis.finviz_data.copy() if main_analysis.finviz_data else {}
                
                # Use specific history for growth
                if style_name == "Growth Investing" and not isinstance(tech_w, Exception) and tech_w:
                    style_analysis.history = tech_w.get("history")
                    style_analysis.atr = tech_w.get("atr", 0.0)
                
                style_strategy = get_trading_style(style_name)
                style_analysis.trading_style = style_strategy.style_name
                
                # Recalculate S/R and setup
                self._calculate_support_resistance(style_analysis)
                style_strategy.calculate_trade_setup(style_analysis)
                
                if style_analysis.suggested_entry and style_analysis.suggested_stop_loss:
                    risk = float(style_analysis.suggested_entry) - float(style_analysis.suggested_stop_loss)
                    if risk > 0:
                        style_analysis.risk_per_unit = risk
                        style_analysis.position_size_units = int(100.0 // risk)
                
                # Score it
                score = style_strategy.score_setup(style_analysis)
                style_scores[style_name] = score
                
                # Save relevant summary
                main_analysis.style_results[style_name] = {
                    "score": score,
                    "trend": style_analysis.market_trend,
                    "entry": style_analysis.suggested_entry,
                    "stop": style_analysis.suggested_stop_loss,
                    "target": style_analysis.target_price or style_analysis.median_price_target,
                    "rr": getattr(style_analysis, 'reward_to_risk', 0.0) or 0.0,
                    "risk_pu": style_analysis.risk_per_unit,
                    "units": style_analysis.position_size_units,
                    "notes": style_analysis.setup_notes,
                    "patterns": [p['pattern'] for p in getattr(style_analysis, 'swing_patterns', [])]
                }
                
                # Save the full analysis object for deep-dive
                main_analysis.style_analyses[style_name] = style_analysis
                
            # 3. Determine best style
            if style_scores:
                best_style = max(style_scores, key=style_scores.get)
                if style_scores[best_style] > 0:
                    main_analysis.best_style = best_style
                    # Populate main analysis with the best style's setup for the dashboard to show it by default
                    best_results = main_analysis.style_results[best_style]
                    main_analysis.trading_style = best_style
                    main_analysis.market_trend = best_results["trend"]
                    main_analysis.suggested_entry = best_results["entry"]
                    main_analysis.suggested_stop_loss = best_results["stop"]
                    main_analysis.target_price = best_results["target"]
                    main_analysis.reward_to_risk = best_results["rr"]
                    main_analysis.setup_notes = best_results["notes"]
                
            return main_analysis
        except Exception as e:
            import traceback
            print(f"CRITICAL ERROR in multi_analyze: {e}")
            traceback.print_exc()
            raise e
    
    def _populate_technical_data(self, analysis: StockAnalysis, data: Dict[str, Any]) -> None:
        """Populate analysis object with technical data"""
        analysis.history = data.get("history")
        analysis.current_price = data.get("current_price", 0.0)
        analysis.open = data.get("open", 0.0)
        analysis.high = data.get("high", 0.0)
        analysis.low = data.get("low", 0.0)
        analysis.close = data.get("close", 0.0)
        analysis.atr = data.get("atr", 0.0)
        analysis.atr_daily = data.get("atr_daily", 0.0)
        analysis.ema20 = data.get("ema20", 0.0)
        analysis.ema50 = data.get("ema50", 0.0)
        analysis.ema200 = data.get("ema200", 0.0)
        analysis.rsi = data.get("rsi", 0.0)
        analysis.macd = data.get("macd", 0.0)
        analysis.macd_signal = data.get("macd_signal", 0.0)
        analysis.bollinger_upper = data.get("bollinger_upper", 0.0)
        analysis.bollinger_lower = data.get("bollinger_lower", 0.0)
        analysis.channel_direction = data.get("channel_direction", "Flat")
        analysis.weekly_ema20 = data.get("weekly_ema20")
        analysis.weekly_ema50 = data.get("weekly_ema50")
        analysis.timestamp = data.get("timestamp")
        
        # Company Info
        analysis.company_name = data.get("company_name")
        analysis.sector = data.get("sector")
        analysis.industry = data.get("industry")
        analysis.quoteType = data.get("quoteType")
        
        # Earnings
        analysis.last_earnings_date = data.get("last_earnings_date")
        analysis.past_earnings_dates = data.get("past_earnings_dates", [])
        analysis.next_earnings_date = data.get("next_earnings_date")
        analysis.days_until_earnings = data.get("days_until_earnings")
        
        analysis.dividend_dates = data.get("dividend_dates", [])
        analysis.insider_buy_dates = data.get("insider_buy_dates", [])
        analysis.insider_sell_dates = data.get("insider_sell_dates", [])
        
        # Financials
        analysis.revenue = data.get("revenue")
        analysis.operating_income = data.get("operating_income")
        analysis.basic_eps = data.get("basic_eps")
        
        # Company info
        analysis.company_name = data.get("company_name")
        analysis.sector = data.get("sector")
        analysis.industry = data.get("industry")
        
        # Checklist fields
        analysis.country = data.get("country")
        analysis.exchange = data.get("exchange")
        analysis.average_volume = data.get("average_volume")
        analysis.analyst_recommendation = data.get("analyst_recommendation")
        analysis.revenue_growth_yoy = data.get("revenue_growth_yoy")
        analysis.op_income_growth_yoy = data.get("op_income_growth_yoy")
        analysis.eps_growth_yoy = data.get("eps_growth_yoy")
        
        # Valuation data
        analysis.book_value = data.get("book_value")
        analysis.free_cash_flow = data.get("free_cash_flow")
        analysis.total_debt = data.get("total_debt")
        analysis.total_cash = data.get("total_cash")
        analysis.shares_outstanding = data.get("shares_outstanding")
        analysis.earnings_growth = data.get("earnings_growth")

    def _calculate_support_resistance(self, analysis: StockAnalysis) -> None:
        """
        Calculate major support and resistance levels using statistical clustering
        and Volume Profile.
        """
        df = analysis.history
        if df is None or len(df) < 20:
            return
            
        import numpy as np
        
        current_price = analysis.current_price
        
        # 1. Volume Profile (Price by Volume)
        min_price = df['Low'].min()
        max_price = df['High'].max()
        
        if pd.notna(min_price) and pd.notna(max_price) and max_price > min_price:
            num_bins = 50
            bins = np.linspace(min_price, max_price, num_bins + 1)
            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            
            # Simple volume distribution
            indices = np.digitize(typical_price.fillna(0), bins)
            
            volume_by_bin = np.zeros(num_bins)
            volumes = df['Volume'].fillna(0).values
            for i in range(len(df)):
                bin_idx = indices[i] - 1
                if 0 <= bin_idx < num_bins:
                    volume_by_bin[bin_idx] += volumes[i]
                    
            # Find High Volume Nodes (HVNs) and Low Volume Nodes (LVNs)
            hvns = []
            lvns = []
            
            # Use 75th percentile of non-zero bins to prevent massive volume spikes from suppressing all other nodes
            non_zero_vols = volume_by_bin[volume_by_bin > 0]
            threshold = np.percentile(non_zero_vols, 75) if len(non_zero_vols) > 0 else 0
            
            for i in range(1, num_bins - 1):
                if volume_by_bin[i] > volume_by_bin[i-1] and volume_by_bin[i] > volume_by_bin[i+1]:
                    if volume_by_bin[i] >= threshold:  # Significant volume peak
                        hvns.append(float((bins[i] + bins[i+1]) / 2))
                elif volume_by_bin[i] < volume_by_bin[i-1] and volume_by_bin[i] < volume_by_bin[i+1]:
                    lvns.append(float((bins[i] + bins[i+1]) / 2))
                    
            analysis.volume_profile_hvns = sorted(hvns)
            analysis.volume_profile_lvns = sorted(lvns)
        
        # 2. Statistical Clustering of daily highs and lows
        highs = df['High'].values
        lows = df['Low'].values
        
        pivot_highs = []
        pivot_lows = []
        
        # Find local extrema (3-day pivot)
        for i in range(1, len(df) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                pivot_highs.append(float(highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                pivot_lows.append(float(lows[i]))
                
        def cluster_levels(levels, threshold_pct=0.02):
            if not levels:
                return []
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                cluster_avg = sum(current_cluster) / len(current_cluster)
                if abs(level - cluster_avg) / cluster_avg <= threshold_pct:
                    current_cluster.append(level)
                else:
                    clusters.append(sum(current_cluster) / len(current_cluster))
                    current_cluster = [level]
                    
            if current_cluster:
                clusters.append(sum(current_cluster) / len(current_cluster))
            return clusters

        clustered_supports = cluster_levels(pivot_lows, 0.02)
        clustered_resistances = cluster_levels(pivot_highs, 0.02)
        
        # Filter for top 3 nearest
        raw_supports = sorted([s for s in clustered_supports if s < current_price])
        raw_resistances = sorted([r for r in clustered_resistances if r > current_price])
        
        # Get strategy rounding logic dynamically
        style_strategy = get_trading_style(analysis.trading_style)
        
        # Apply psychological integer rounding
        supports = sorted(list(set([style_strategy._apply_smart_rounding(s) for s in raw_supports])))
        resistances = sorted(list(set([style_strategy._apply_smart_rounding(r) for r in raw_resistances])))
        
        analysis.support_levels = supports[-3:] if supports else []
        analysis.resistance_levels = resistances[:3] if resistances else []
