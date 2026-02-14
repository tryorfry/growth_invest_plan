"""Insider trading data source using SEC EDGAR"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class InsiderSource:
    """Fetch insider trading data from SEC EDGAR"""
    
    async def fetch_insider_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch recent insider trading activity.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with insider trading data
        """
        try:
            # Use a simpler approach - get from yfinance first
            import yfinance as yf
            stock = yf.Ticker(ticker)
            
            # Get insider transactions
            try:
                insider_txns = stock.insider_transactions
                if insider_txns is not None and not insider_txns.empty:
                    recent_txns = insider_txns.head(10)
                    
                    # Calculate net buying/selling
                    buys = recent_txns[recent_txns['Transaction'] == 'Buy']['Shares'].sum() if 'Transaction' in recent_txns.columns else 0
                    sells = recent_txns[recent_txns['Transaction'] == 'Sale']['Shares'].sum() if 'Transaction' in recent_txns.columns else 0
                    
                    return {
                        'recent_transactions': len(recent_txns),
                        'total_shares_bought': buys,
                        'total_shares_sold': sells,
                        'net_insider_activity': buys - sells,
                        'transactions': recent_txns.to_dict('records') if len(recent_txns) > 0 else [],
                        'fetched_at': datetime.now()
                    }
            except:
                pass
            
            # Get insider ownership percentage
            info = stock.info
            insider_ownership = info.get('heldPercentInsiders', 0) * 100 if info.get('heldPercentInsiders') else 0
            
            return {
                'insider_ownership_pct': insider_ownership,
                'recent_transactions': 0,
                'total_shares_bought': 0,
                'total_shares_sold': 0,
                'net_insider_activity': 0,
                'transactions': [],
                'fetched_at': datetime.now()
            }
            
        except Exception as e:
            print(f"Error fetching insider data for {ticker}: {e}")
            return {
                'insider_ownership_pct': 0,
                'recent_transactions': 0,
                'error': str(e)
            }
