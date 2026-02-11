"""Formatters for displaying stock analysis results"""

from typing import Optional
from .analyzer import StockAnalysis


class AnalysisFormatter:
    """Formats StockAnalysis objects for console output"""
    
    @staticmethod
    def format_number(value: Optional[float], decimals: int = 2) -> str:
        """Format a number with specified decimal places"""
        if value is None:
            return "N/A"
        return f"{value:.{decimals}f}"
    
    @staticmethod
    def format_currency(value: Optional[float]) -> str:
        """Format large currency values with B/M suffixes"""
        if value is None or not isinstance(value, (int, float)):
            return "N/A"
        
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.2f}"
    
    @staticmethod
    def print_analysis(analysis: StockAnalysis) -> None:
        """
        Print formatted stock analysis to console.
        
        Args:
            analysis: StockAnalysis object to display
        """
        fmt = AnalysisFormatter
        
        # Header
        print(f"\n--- Analysis for {analysis.ticker} ({analysis.timestamp}) ---")
        print(f"Current Price: {fmt.format_number(analysis.current_price)}")
        print(f"Open: {fmt.format_number(analysis.open)} | "
              f"High: {fmt.format_number(analysis.high)} | "
              f"Low: {fmt.format_number(analysis.low)} | "
              f"Close: {fmt.format_number(analysis.close)}")
        print("-" * 30)
        
        # Technical indicators
        print(f"ATR (14):   {fmt.format_number(analysis.atr)}")
        print(f"EMA 20:     {fmt.format_number(analysis.ema20)}")
        print(f"EMA 50:     {fmt.format_number(analysis.ema50)}")
        print(f"EMA 200:    {fmt.format_number(analysis.ema200)}")
        
        # Earnings
        if analysis.last_earnings_date:
            print(f"Last Earnings: {analysis.last_earnings_date.date()}")
        
        # Analyst targets
        if analysis.median_price_target:
            print(f"Median MBP (Post-Earnings): ${fmt.format_number(analysis.median_price_target)}")
        
        # Finviz data
        if analysis.finviz_data:
            fmt._print_finviz_section(analysis.finviz_data)
        
        # Financials
        fmt._print_financials_section(analysis)
    
    @staticmethod
    def _print_finviz_section(data: dict) -> None:
        """Print Finviz fundamental data section"""
        print("\n--- Finviz Data ---")
        print(f"Market Cap: {data.get('Market Cap', 'N/A')}")
        print(f"Analysts Recom: {data.get('Recom', 'N/A')}")
        print(f"Inst Own: {data.get('Inst Own', 'N/A')}")
        print(f"Avg Volume: {data.get('Avg Volume', 'N/A')}")
        print(f"ROE: {data.get('ROE', 'N/A')} | ROA: {data.get('ROA', 'N/A')}")
        print(f"EPS Growth (This Y): {data.get('EPS this Y', 'N/A')}")
        print(f"EPS Growth (Next Y): {data.get('EPS next Y', 'N/A')}")
        print(f"EPS Growth (Next 5Y): {data.get('EPS next 5Y', 'N/A')}")
        print(f"P/E: {data.get('P/E', 'N/A')} | "
              f"Fwd P/E: {data.get('Forward P/E', 'N/A')} | "
              f"PEG: {data.get('PEG', 'N/A')}")
    
    @staticmethod
    def _print_financials_section(analysis: StockAnalysis) -> None:
        """Print financial data section"""
        fmt = AnalysisFormatter
        
        if not any([analysis.revenue, analysis.operating_income, analysis.basic_eps]):
            return
        
        print("\n--- Fundamentals (Macrotrends Context) ---")
        print(f"Latest Revenue (Quarterly): {fmt.format_currency(analysis.revenue)}")
        print(f"Op Income (Quarterly): {fmt.format_currency(analysis.operating_income)}")
        print(f"Basic EPS (Quarterly): {fmt.format_number(analysis.basic_eps)}")
        
        if analysis.next_earnings_date:
            date_str = analysis.next_earnings_date.date()
            days = analysis.days_until_earnings
            print(f"Next Earnings Date: {date_str} ({days} days left)")
            
            if analysis.has_earnings_warning():
                print("⚠️ WARNING: Earnings in less than 10 days! Trade with caution.")
