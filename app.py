#!/usr/bin/env python
"""
Growth Investment Plan Analysis Tool - Main Entry Point

Refactored version using design patterns for better maintainability.
"""

import sys
from src.analyzer import StockAnalyzer
from src.formatter import AnalysisFormatter

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    """Main entry point for the application"""
    # Get ticker from command line or prompt
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter stock ticker symbol: ").upper()
    
    # Create analyzer and run analysis
    analyzer = StockAnalyzer()
    analysis = analyzer.analyze(ticker, verbose=True)
    
    # Display results
    if analysis:
        AnalysisFormatter.print_analysis(analysis)
    else:
        print(f"Failed to analyze {ticker}")
        sys.exit(1)


if __name__ == "__main__":
    main()
