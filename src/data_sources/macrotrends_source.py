"""Macrotrends data source for financial statements"""

import re
import json
import asyncio
from typing import Dict, Any, Optional, List
from curl_cffi import requests
from bs4 import BeautifulSoup
from .base import FundamentalDataSource

class MacrotrendsSource(FundamentalDataSource):
    """Scrapes financial data from Macrotrends with curl_cffi for bot bypass"""
    
    BASE_URL = "https://www.macrotrends.net/stocks/charts"
    TIMEOUT = 15
    
    def get_source_name(self) -> str:
        return "Macrotrends"

    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch core financials from Macrotrends.
        Tries to get Revenue, Operating Income, and EPS (Diluted).
        """
        loop = asyncio.get_running_loop()
        # We'll use a wrapper to run the synchronous scraping logic in an executor
        from functools import partial
        return await loop.run_in_executor(None, partial(self._scrape_all, ticker=ticker))

    def _scrape_all(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Scrape multiple metrics from Macrotrends"""
        results = {}
        
        # 1. Get the base URL (resolves the company name slug)
        base_search_url = f"{self.BASE_URL}/{ticker}"
        try:
            response = requests.get(base_search_url, impersonate="chrome110", timeout=self.TIMEOUT, follow_redirects=True)
            if response.status_code != 200:
                return None
            
            # The URL will now look like macrotrends.net/stocks/charts/AAPL/apple/revenue
            # We need the portion after charts/
            final_url = response.url
            match = re.search(r'charts/([^/]+/[^/]+)', final_url)
            if not match:
                return None
            
            company_path = match.group(1) # e.g. "AAPL/apple"
            
            # 2. Fetch specific metrics
            # Note: Macrotrends often has all data in the 'financial-statements' or specifically named pages
            metrics_to_fetch = {
                'revenue': 'revenue',
                'operating_income': 'operating-income',
                'eps_diluted': 'eps-earnings-per-share-diluted'
            }
            
            for key, metric_slug in metrics_to_fetch.items():
                url = f"{self.BASE_URL}/{company_path}/{metric_slug}"
                metric_data = self._scrape_metric(url)
                if metric_data:
                    results[key] = metric_data
            
            return results if results else None
            
        except Exception as e:
            print(f"Macrotrends Scrape Error for {ticker}: {e}")
            return None

    def _scrape_metric(self, url: str) -> Optional[float]:
        """Scrape the latest quarterly value for a specific metric page"""
        try:
            response = requests.get(url, impersonate="chrome110", timeout=self.TIMEOUT)
            if response.status_code != 200:
                return None
            
            # Method 1: Look for 'original_data' in script tags (reliable)
            data_match = re.search(r'var original_data = (\[.*?\]);', response.text, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    if data and len(data) > 0:
                        # Macrotrends JSON usually has "v1" as the value and "field_name" as the date/label
                        # We want the most recent quarterly value. Data is usually sorted by date.
                        # We tipically want the last object in the list if it's chronological, 
                        # or first if reverse chronological.
                        # Let's inspect the first element.
                        latest = data[0]
                        val = latest.get('v1') or latest.get('v2') # Macrotrends uses v1, v2...
                        if val:
                            return float(val)
                except:
                    pass

            # Method 2: Fallback to HTML table parsing
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for the second table (Quarterly)
            tables = soup.find_all("table", class_="historical_data_table")
            if len(tables) >= 2:
                quarterly_table = tables[1]
                rows = quarterly_table.find_all("tr")
                if len(rows) > 1:
                    first_row_cols = rows[1].find_all("td")
                    if len(first_row_cols) >= 2:
                        val_str = first_row_cols[1].get_text(strip=True)
                        return self._parse_currency(val_str)
            
            return None
        except:
            return None

    def _parse_currency(self, val_str: str) -> Optional[float]:
        """Convert string like '$123,456.00' to float"""
        try:
            clean = re.sub(r'[^\d.-]', '', val_str)
            return float(clean) if clean else None
        except:
            return None
