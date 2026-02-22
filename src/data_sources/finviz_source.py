"""Finviz data source for fundamental metrics"""

from typing import Dict, Any, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
import streamlit as st

from .base import FundamentalDataSource


class FinvizSource(FundamentalDataSource):
    """Scrapes fundamental data from Finviz"""
    
    BASE_URL = "https://finviz.com/quote.ashx"
    TIMEOUT = 10
    
    def get_source_name(self) -> str:
        return "Finviz"
    
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Scrape fundamental data from Finviz asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with fundamental metrics or None if fetch fails
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_sync, ticker)

    @st.cache_data(ttl=3600)
    def _fetch_sync(_self, ticker: str) -> Optional[Dict[str, Any]]:
        """Synchronous fetch logic for thread execution"""
        url = f"{_self.BASE_URL}?t={ticker}&p=d"
        
        try:
            response = requests.get(url, impersonate="chrome110", timeout=_self.TIMEOUT)
            
            if response.status_code != 200:
                print(f"Failed to fetch Finviz data: HTTP {response.status_code}")
                return None
            
            return _self._parse_snapshot_table(response.content)
            
        except Exception as e:
            print(f"Error fetching Finviz data: {e}")
            return None
    
    def _parse_snapshot_table(_self, html_content: bytes) -> Dict[str, str]:
        """
        Parse the Finviz snapshot table.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dictionary mapping metric names to values
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        snapshot = soup.find("table", class_="snapshot-table2")
        
        if not snapshot:
            print("Finviz snapshot table not found")
            return {}
        
        data = {}
        rows = snapshot.find_all("tr")
        
        for row in rows:
            cols = row.find_all("td")
            # Table structure: Label | Value | Label | Value ...
            for i in range(0, len(cols), 2):
                if i + 1 < len(cols):
                    key = cols[i].get_text(strip=True)
                    value = cols[i + 1].get_text(strip=True)
                    data[key] = value
        
        return data
