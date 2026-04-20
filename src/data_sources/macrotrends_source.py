"""Macrotrends data source for financial statements"""

import re
import json
import asyncio
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from .base import FundamentalDataSource

class MacrotrendsSource(FundamentalDataSource):
    """Scrapes financial data from Macrotrends with curl_cffi for bot bypass"""
    
    BASE_URL = "https://www.macrotrends.net/stocks/charts"
    TIMEOUT = 8
    
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
            # Inject Referer to look more like a browser search
            headers = {
                "Referer": "https://www.google.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }
            response = self._get_response_sync(base_search_url, allow_redirects=True, headers=headers)
            if not response:
                return None
            
            # The URL will now look like macrotrends.net/stocks/charts/AAPL/apple/revenue
            # We need the portion after charts/
            final_url = response.url
            match = re.search(r'charts/([^/]+/[^/]+)', final_url)
            if not match:
                return None
            
            company_path = match.group(1) # e.g. "AAPL/apple"
            
            # 2. Fetch specific metrics
            metrics_to_fetch = {
                'revenue': 'revenue',
                'operating_income': 'operating-income',
                'eps_diluted': 'eps-earnings-per-share-diluted'
            }
            
            for key, metric_slug in metrics_to_fetch.items():
                url = f"{self.BASE_URL}/{company_path}/{metric_slug}"
                metric_history = self._scrape_metric_history(url)
                if metric_history and len(metric_history) >= 5:
                    latest = metric_history[0]
                    prev_year = metric_history[4] # 4 quarters ago
                    if latest and prev_year and prev_year != 0:
                        results[f"{key}_growth"] = (latest - prev_year) / abs(prev_year)
                    results[key] = latest
                elif metric_history:
                    results[key] = metric_history[0]
            
            return results if results else None
            
        except Exception as e:
            print(f"Macrotrends Scrape Error for {ticker}: {e}")
            return None

    def _scrape_metric(self, url: str) -> Optional[float]:
        """Scrape the latest quarterly value for a specific metric page"""
        vals = self._scrape_metric_history(url)
        return vals[0] if vals else None

    def _scrape_metric_history(self, url: str) -> List[float]:
        """Scrape all historical quarterly values for a specific metric page"""
        try:
            html = self._make_request_sync(url)
            if not html:
                return []
            
            # Method 1: Look for 'original_data' in script tags (reliable)
            data_match = re.search(r'var original_data = (\[.*?\]);', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    results = []
                    for item in data:
                        val = item.get('v1') or item.get('v2') or item.get('v3')
                        if val is not None:
                            results.append(float(val))
                    return results
                except:
                    pass

            # Method 2: Fallback to HTML table parsing
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all("table", class_="historical_data_table")
            if len(tables) >= 2:
                quarterly_table = tables[1]
                rows = quarterly_table.find_all("tr")
                results = []
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        val = self._parse_currency(cols[1].get_text(strip=True))
                        if val is not None:
                            results.append(val)
                return results
            
            return []
        except:
            return []

    def _parse_currency(self, val_str: str) -> Optional[float]:
        """Convert string like '$123,456.00' to float"""
        try:
            clean = re.sub(r'[^\d.-]', '', val_str)
            return float(clean) if clean else None
        except:
            return None
