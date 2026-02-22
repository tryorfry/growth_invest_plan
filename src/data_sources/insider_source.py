"""Source for fetching and analyzing C-Suite Insider Trading activity"""

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, Any, List

class InsiderSource:
    """Fetches insider transaction metrics such as Net Accumulation and key trades"""
    
    @st.cache_data(ttl=3600)
    def fetch_insider_activity(_self, ticker: str) -> Dict[str, Any]:
        """
        Fetches 6-month aggregate purchases/sales and a recent history of trades.
        
        Args:
            ticker: Stock symbol to analyze.
            
        Returns:
            Dict containing aggregation metrics and recent transactions list.
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Fetch aggregate purchases over last 6 months
            purchases_df = stock.insider_purchases
            transactions_df = stock.insider_transactions
            
            result = {
                "six_month_buys": 0,
                "six_month_sales": 0,
                "net_shares_purchased": 0,
                "total_insider_shares": 0,
                "recent_transactions": []
            }
            
            if purchases_df is not None and not purchases_df.empty:
                # yFinance columns: 'Insider Purchases Last 6m', 'Shares', 'Trans'
                col_name = purchases_df.columns[0]
                
                for _, row in purchases_df.iterrows():
                    metric = str(row[col_name]).strip()
                    shares = float(row.get('Shares', 0.0)) if pd.notna(row.get('Shares')) else 0.0
                    
                    if metric == 'Purchases':
                        result["six_month_buys"] = shares
                    elif metric == 'Sales':
                        result["six_month_sales"] = shares
                    elif metric == 'Net Shares Purchased (Sold)':
                        result["net_shares_purchased"] = shares
                    elif metric == 'Total Insider Shares Held':
                        result["total_insider_shares"] = shares
                        
            if transactions_df is not None and not transactions_df.empty:
                # Get the top 15 most recent transactions
                recent = transactions_df.head(15).copy()
                
                for _, row in recent.iterrows():
                    start_date = row.get('Start Date')
                    date_str = start_date.strftime('%Y-%m-%d') if pd.notna(start_date) else "Unknown"
                    
                    result["recent_transactions"].append({
                        "date": date_str,
                        "insider": str(row.get('Insider', 'Unknown')),
                        "position": str(row.get('Position', 'Unknown')),
                        "shares": int(row.get('Shares', 0)) if pd.notna(row.get('Shares')) else 0,
                        "value": float(row.get('Value', 0.0)) if pd.notna(row.get('Value')) else 0.0
                    })
                    
            return result
            
        except Exception as e:
            print(f"Error fetching insider data for {ticker}: {e}")
            return {
                "six_month_buys": 0,
                "six_month_sales": 0,
                "net_shares_purchased": 0,
                "total_insider_shares": 0,
                "recent_transactions": [],
                "error": str(e)
            }
