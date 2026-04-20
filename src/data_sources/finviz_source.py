"""Finviz data source for fundamental metrics"""

from typing import Dict, Any, Optional
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
        url = f"{_self.BASE_URL}?t={ticker.upper()}"
        
        # Enhanced headers to bypass bot blocks
        headers = {
            "Referer": "https://finviz.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1"
        }
        
        resp = _self._get_response_sync(url, headers=headers)
        if resp and resp.status_code == 200:
            return _self._parse_snapshot_table(resp.text)
        return None
    
    def _parse_snapshot_table(_self, html_content: Any) -> Dict[str, str]:
        """
        Parse the Finviz snapshot table and header info (Country/Exchange).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {}
        
        # 1. Extract Header Info (Sector | Industry | Country | Exchange)
        # Usually found in a list above the main table
        links = soup.find_all("a", class_="tab-link")
        if len(links) >= 4:
            # Structure: [Sector, Industry, Country, Exchange]
            data['Sector'] = links[0].get_text(strip=True)
            data['Industry'] = links[1].get_text(strip=True)
            data['Country'] = links[2].get_text(strip=True)
            data['Exchange'] = links[3].get_text(strip=True)

        # 2. Extract Main Table
        snapshot = soup.find("table", class_="snapshot-table2")
        if snapshot:
            rows = snapshot.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                for i in range(0, len(cols), 2):
                    if i + 1 < len(cols):
                        key = cols[i].get_text(strip=True)
                        value = cols[i + 1].get_text(strip=True)
                        data[key] = value
        
        return data
