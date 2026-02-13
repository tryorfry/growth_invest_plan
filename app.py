import sys
import argparse
import asyncio
import os
from typing import List, Optional

from src.analyzer import StockAnalyzer, StockAnalysis
from src.formatter import AnalysisFormatter
from src.visualization import ChartGenerator
from src.exporter import export_to_csv
from src.database import Database
from src.models import Analysis

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
    parser.add_argument("--no-db", action="store_true", help="Skip database storage")
    
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
    
    # Initialize database
    db = None
    if not args.no_db:
        db = Database("stock_analysis.db")
        db.init_db()
    
    # Run analysis concurrently
    tasks = [analyze_ticker(analyzer, chart_generator, t) for t in tickers]
    results = await asyncio.gather(*tasks)
    
    # Filter valid results
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        # Export to CSV
        export_to_csv(valid_results, args.csv)
        
        # Save to database
        if db:
            for analysis in valid_results:
                save_analysis_to_db(db, analysis)
            print(f"Saved {len(valid_results)} analyses to database")
    else:
        print("No successful analyses.")

def save_analysis_to_db(db: Database, analysis: StockAnalysis):
    """Save analysis results to database"""
    with db.get_session() as session:
        # Get or create stock with sector/industry
        stock = db.get_or_create_stock(
            session, 
            analysis.ticker,
            name=analysis.company_name,
            sector=analysis.sector,
            industry=analysis.industry
        )
        
        analysis_record = Analysis(
            stock_id=stock.id,
            timestamp=analysis.timestamp,
            current_price=analysis.current_price,
            open_price=analysis.open,
            high=analysis.high,
            low=analysis.low,
            close=analysis.close,
            atr=analysis.atr,
            ema20=analysis.ema20,
            ema50=analysis.ema50,
            ema200=analysis.ema200,
            rsi=analysis.rsi,
            macd=analysis.macd,
            macd_signal=analysis.macd_signal,
            bollinger_upper=analysis.bollinger_upper,
            bollinger_lower=analysis.bollinger_lower,
            last_earnings_date=analysis.last_earnings_date,
            next_earnings_date=analysis.next_earnings_date,
            days_until_earnings=analysis.days_until_earnings,
            revenue=analysis.revenue,
            operating_income=analysis.operating_income,
            basic_eps=analysis.basic_eps,
            median_price_target=analysis.median_price_target,
            news_sentiment=analysis.news_sentiment,
            news_summary=analysis.news_summary
        )
        
        session.add(analysis_record)
        session.commit()

if __name__ == "__main__":
    asyncio.run(main())
