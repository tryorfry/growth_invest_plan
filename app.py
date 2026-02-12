import sys
import argparse
import asyncio
import os
from typing import List

from src.analyzer import StockAnalyzer, StockAnalysis
from src.formatter import AnalysisFormatter
from src.visualization import ChartGenerator
from src.exporter import export_to_csv

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def analyze_ticker(analyzer: StockAnalyzer, chart_generator: ChartGenerator, ticker: str) -> Optional[StockAnalysis]:
    """Analyze a single ticker and generate artifacts"""
    try:
        analysis = await analyzer.analyze(ticker, verbose=True)
        if analysis:
            AnalysisFormatter.print_analysis(analysis)
            
            # Print News Section
            if analysis.news_summary:
                print(f"News Sentiment: {analysis.news_summary}")
                
            # Generate Chart
            chart_path = chart_generator.generate_chart(analysis)
            if chart_path:
                print(f"Chart saved to: {chart_path}")
                
            return analysis
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
    return None

async def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Growth Investment Stock Analyzer")
    parser.add_argument("tickers", nargs="*", help="Stock ticker symbols (space separated)")
    parser.add_argument("--file", "-f", help="File containing list of tickers (one per line)")
    parser.add_argument("--csv", "-c", help="Output CSV file path", default="analysis_results.csv")
    parser.add_argument("--charts-dir", help="Directory to save charts", default="charts")
    
    args = parser.parse_args()
    
    tickers = []
    
    # parse command line tickers (handle comma separation if user does AAPL,NVDA)
    for t in args.tickers:
        if ',' in t:
            tickers.extend([x.strip().upper() for x in t.split(',') if x.strip()])
        else:
            tickers.append(t.upper())
            
    # parse file
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r') as f:
                for line in f:
                    t = line.strip().upper()
                    if t and not t.startswith('#'):
                        tickers.append(t)
        else:
            print(f"Error: File {args.file} not found.")
            
    if not tickers:
        user_input = input("Enter stock ticker symbols (comma or space separated): ")
        if user_input.strip():
            # Handle comma or space
            parts = user_input.replace(',', ' ').split()
            tickers.extend([p.upper() for p in parts if p.strip()])
    
    if not tickers:
        print("No tickers provided. Exiting.")
        sys.exit(1)
        
    print(f"Analyzing {len(tickers)} stocks: {', '.join(tickers)}")
    
    analyzer = StockAnalyzer()
    chart_generator = ChartGenerator(output_dir=args.charts_dir)
    
    # Run analysis concurrently
    tasks = [analyze_ticker(analyzer, chart_generator, t) for t in tickers]
    results = await asyncio.gather(*tasks)
    
    # Filter valid results
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        export_to_csv(valid_results, args.csv)
    else:
        print("No successful analyses.")

if __name__ == "__main__":
    asyncio.run(main())
