
import yfinance as yf
import pandas as pd
from src.pattern_recognition import PatternRecognition

def test_logic():
    print("Testing pattern recognition logic with synthetic data...")
    # Create synthetic data for a Hammer
    # Hammer: small body, long lower shadow, little/no upper shadow
    # Appearing in a downtrend
    data = {
        'Open': [100, 95, 90],
        'High': [102, 96, 91],
        'Low': [98, 92, 80],
        'Close': [97, 91, 89],
        'Volume': [1000, 1000, 1000]
    }
    df = pd.DataFrame(data, index=pd.date_range("2023-01-01", periods=3))
    
    detector = PatternRecognition()
    patterns = detector.detect_patterns(df)
    
    print(f"Patterns found: {len(patterns)}")
    for p in patterns:
        print(f"Pattern: {p['pattern']}, Date: {p['date']}")

if __name__ == "__main__":
    test_logic()
