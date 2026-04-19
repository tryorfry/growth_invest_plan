import asyncio
import os
import sys

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit caching for terminal run
import streamlit as st
def mock_cache(ttl=0):
    def decorator(f):
        return f
    return decorator
st.cache_data = mock_cache

from src.data_sources.macro_source import MacroSource

def test_fetch():
    print("Testing MacroSource.fetch_global_snapshot()...")
    data = MacroSource.fetch_global_snapshot()
    print(f"Fetched {len(data)} items.")
    for item in data[:3]:
        print(f" - {item['name']}: {item['value']} ({item['pct_change']:.2f}%)")

if __name__ == "__main__":
    test_fetch()
