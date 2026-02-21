"""Source for Institutional (Whale) Ownership data"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional

class InstitutionalSource:
    """Fetches institutional and mutual fund holdings for a given ticker."""
    
    def fetch_institutional_holders(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches the major institutional holders from Yahoo Finance.
        Returns a dictionary containing top institutional and mutual fund holders.
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Retrieve dataframes from yfinance
            inst_df = stock.institutional_holders
            mut_df = stock.mutualfund_holders
            maj_df = stock.major_holders
            
            result = {
                "institutional_holders": [],
                "mutualfund_holders": [],
                "major_holdings_breakdown": {}
            }
            
            # Parse Major Holders (Breakdown of % held by insiders vs institutions)
            if isinstance(maj_df, pd.DataFrame) and not maj_df.empty:
                for _, row in maj_df.iterrows():
                    if len(row) >= 2:
                        val = row.iloc[0]
                        desc = str(row.iloc[1]).strip()
                        result["major_holdings_breakdown"][desc] = val
                    elif len(row) == 1:
                        # Sometimes yfinance puts description in index and value in column
                        val = row.iloc[0]
                        desc = str(row.name).strip()
                        result["major_holdings_breakdown"][desc] = val
                    
            # Parse Institutional Holders
            if isinstance(inst_df, pd.DataFrame) and not inst_df.empty:
                # Common columns: 'Holder', 'Shares', 'Date Reported', '% Out', 'Value'
                for _, row in inst_df.iterrows():
                    holder_data = {
                        "holder": row.get('Holder', 'Unknown'),
                        "shares": int(row.get('Shares', 0)) if pd.notna(row.get('Shares')) else 0,
                        "date_reported": str(row.get('Date Reported', '')).split(' ')[0],
                        "pct_held": float(row.get('% Out', 0)) if pd.notna(row.get('% Out')) else 0.0,
                        "value": float(row.get('Value', 0)) if pd.notna(row.get('Value')) else 0.0
                    }
                    result["institutional_holders"].append(holder_data)
                    
            # Parse Mutual Fund Holders
            if isinstance(mut_df, pd.DataFrame) and not mut_df.empty:
                for _, row in mut_df.iterrows():
                    holder_data = {
                        "holder": row.get('Holder', 'Unknown'),
                        "shares": int(row.get('Shares', 0)) if pd.notna(row.get('Shares')) else 0,
                        "date_reported": str(row.get('Date Reported', '')).split(' ')[0],
                        "pct_held": float(row.get('% Out', 0)) if pd.notna(row.get('% Out')) else 0.0,
                        "value": float(row.get('Value', 0)) if pd.notna(row.get('Value')) else 0.0
                    }
                    result["mutualfund_holders"].append(holder_data)
                    
            return result
            
        except Exception as e:
            print(f"Error fetching institutional holders for {ticker}: {e}")
            return None
