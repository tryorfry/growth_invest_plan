import asyncio
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.analyzer import StockAnalyzer
from src.logic.scorer import ChecklistScorer

async def diag():
    analyzer = StockAnalyzer()
    ticker = "GOOG"
    print(f"--- Diagnosing {ticker} ---")
    
    # 1. Test direct YFinance fetch
    print(f"Fetching {ticker} via StockAnalyzer.analyze(lite=True)...")
    analysis = await analyzer.analyze(ticker, lite=True)
    
    if not analysis:
        print("X Analysis returned None!")
        return

    print(f"Analysis successful for {ticker}")
    print(f"Datasource Health: {analysis.datasource_health}")
    
    # Check finviz_data (should contain fallbacks if Finviz is blocked)
    fd = analysis.finviz_data
    print(f"Fundamental Data Keys: {list(fd.keys())}")
    for k in ['Market Cap', 'ROE', 'P/E', 'PEG', 'EPS next 5Y']:
        print(f"  {k}: {fd.get(k)}")
        
    # 2. Test Scoring
    print("Running ChecklistScorer...")
    score, total, details = ChecklistScorer.calculate_score(analysis)
    print(f"Overall Score: {score}/{total}")
    for pt, res in details.items():
        print(f"  [{'PASS' if res['pass'] else 'FAIL'}] {res['label']}")

if __name__ == "__main__":
    asyncio.run(diag())
