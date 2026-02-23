
import yfinance as yf
import pandas as pd
from src.pattern_recognition import PatternRecognition

def debug_patterns(ticker):
    print(f"Debugging patterns for {ticker}...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="3mo")
    
    if df.empty:
        print("Empty dataframe")
        return
        
    print(f"Data columns: {df.columns.tolist()}")
    print(f"First few rows:\n{df.head()}")
    
    detector = PatternRecognition()
    patterns = detector.detect_patterns(df)
    
    print(f"\nTotal patterns found: {len(patterns)}")
    for p in patterns:
        print(f"Date: {p['date']}, Pattern: {p['pattern']}, Signal: {p['signal']}, Price: {p['price']:.2f}")

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    debug_patterns(ticker)
