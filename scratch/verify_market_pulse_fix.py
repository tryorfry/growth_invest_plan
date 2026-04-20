import asyncio
import sys
import os
import pandas as pd

# Add root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.macro_source import MacroSource

def test_macro_data():
    print("--- Testing MacroSource.fetch_macro_data() ---")
    data = MacroSource().fetch_macro_data()
    if not data:
        print("❌ FAILED: No data returned")
        return
    
    expected_keys = ['10Y_Yield', '5Y_Yield', 'Short_Yield', 'VIX', 'SPY', 'Dollar_Index', 'Yield_Spread']
    for key in expected_keys:
        if key in data:
            print(f"✅ FOUND: {key:15} | {data[key]}")
        else:
            print(f"❌ MISSING: {key}")

def test_sector_data():
    print("\n--- Testing MacroSource.fetch_sector_data() ---")
    data = MacroSource().fetch_sector_data()
    if not data:
        print("❌ FAILED: No data returned")
        return
    
    print(f"✅ FOUND {len(data)} sectors")
    for name, perf in data.items():
        print(f"   {name:20} | {perf:+.2f}%")

def test_historical():
    print("\n--- Testing MacroSource.fetch_historical_macro('10Y_Yield') ---")
    hist = MacroSource().fetch_historical_macro('10Y_Yield')
    if hist is not None and not hist.empty:
        print(f"✅ FOUND: {len(hist)} days of data")
    else:
        print("❌ FAILED: No historical data")

if __name__ == "__main__":
    test_macro_data()
    test_sector_data()
    test_historical()
