"""
Utility for calculating price correlations between multiple tickers.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from src.analyzer import StockAnalysis

def calculate_correlation_matrix(analyses: List[StockAnalysis]) -> pd.DataFrame:
    """
    Calculates a correlation matrix based on closing prices of provided analyses.
    Uses daily closing prices for the period where all tickers have data (intersection).
    """
    if not analyses or len(analyses) < 2:
        return pd.DataFrame()

    # Create a combined dataframe of closing prices
    price_data = {}
    for a in analyses:
        if a.history is not None and not a.history.empty and 'Close' in a.history.columns:
            price_data[a.ticker] = a.history['Close']

    if not price_data:
        return pd.DataFrame()

    df = pd.DataFrame(price_data)
    
    # Calculate percentage change for correlation (more stable than absolute prices)
    returns_df = df.pct_change().dropna()
    
    if returns_df.empty:
        return pd.DataFrame()
        
    return returns_df.corr()
