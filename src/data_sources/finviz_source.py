"""Finviz data source for fundamental metrics"""

from typing import Dict, Any, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup

from .base import FundamentalDataSource


class FinvizSource(FundamentalDataSource):
    """Scrapes fundamental data from Finviz"""
    
    BASE_URL = "https://finviz.com/quote.ashx"
    TIMEOUT = 10
    
    def get_source_name(self) -> str:
        return "Finviz"
    
    def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Scrape fundamental data from Finviz.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with fundamental metrics or None if fetch fails
        """
        url = f"{self.BASE_URL}?t={ticker}&p=d"
        
        try:
            response = requests.get(url, impersonate="chrome110", timeout=self.TIMEOUT)
            
            if response.status_code != 200:
                print(f"Failed to fetch Finviz data: HTTP {response.status_code}")
                return None
            
            return self._parse_snapshot_table(response.content)
            
        except Exception as e:
            print(f"Error fetching Finviz data: {e}")
            return None
    
    def _parse_snapshot_table(self, html_content: bytes) -> Dict[str, str]:
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
