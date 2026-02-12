"""MarketBeat data source for analyst price targets"""

from typing import Dict, Any, Optional
from datetime import datetime
import statistics
import re
import pandas as pd
from curl_cffi import requests
from bs4 import BeautifulSoup

from .base import AnalystDataSource


class MarketBeatSource(AnalystDataSource):
    """Scrapes analyst price targets from MarketBeat"""
    
    BASE_URL = "https://www.marketbeat.com/stocks"
    EXCHANGES = ["NASDAQ", "NYSE"]
    TIMEOUT = 10
    
    def get_source_name(self) -> str:
        return "MarketBeat"
    
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch analyst price targets from MarketBeat asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            **kwargs: Must include 'last_earnings_date' (pd.Timestamp)
            
        Returns:
            Dictionary with median price target or None
        """
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        last_earnings_date = kwargs.get('last_earnings_date')
        
        # Run blocking call in executor
        # Use partial to pass kwargs if needed, but here we extract specific args
        return await loop.run_in_executor(
            None, 
            partial(self._fetch_sync, ticker=ticker, last_earnings_date=last_earnings_date)
        )

    def _fetch_sync(self, ticker: str, last_earnings_date: Any) -> Optional[Dict[str, Any]]:
        """Synchronous fetch logic for thread execution"""
        if not last_earnings_date:
            print("MarketBeat requires last_earnings_date parameter")
            return None
        
        # Try different exchanges
        for exchange in self.EXCHANGES:
            url = f"{self.BASE_URL}/{exchange}/{ticker}/price-target/"
            
            try:
                response = requests.get(url, impersonate="chrome110", timeout=self.TIMEOUT)
                
                if response.status_code == 200:
                    median_target = self._parse_price_targets(
                        response.content, 
                        last_earnings_date
                    )
                    
                    if median_target is not None:
                        return {"median_price_target": median_target}
                        
                elif response.status_code == 404:
                    continue  # Try next exchange
                    
            except Exception as e:
                print(f"Error fetching MarketBeat data: {e}")
                return None
        
        print(f"Could not find MarketBeat page for {ticker}")
        return None
    
    def _parse_price_targets(
        self, 
        html_content: bytes, 
        last_earnings_date: pd.Timestamp
    ) -> Optional[float]:
        """
        Parse price targets from MarketBeat table.
        
        Args:
            html_content: Raw HTML content
            last_earnings_date: Filter ratings after this date
            
        Returns:
            Median price target or None
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        price_targets = []
        
        # Find the ratings table
        rating_table = self._find_ratings_table(soup)
        if not rating_table:
            return None
        
        rows = rating_table.find_all("tr")
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 6:
                continue
            
            try:
                # Parse date (column 0)
                date_str = cols[0].get_text(strip=True)
                rating_date = datetime.strptime(date_str, "%m/%d/%Y")
                rating_date = rating_date.replace(tzinfo=last_earnings_date.tzinfo)
                
                # Skip ratings before earnings
                if rating_date < last_earnings_date:
                    continue
                
                # Parse price target (column 5)
                price_target_str = cols[5].get_text(strip=True)
                if not price_target_str:
                    continue
                
                # Extract numeric values (handles "$300.00" or "$300.00 -> $320.00")
                matches = re.findall(r'\$?(\d+\.\d{2})', price_target_str)
                if matches:
                    # Take the latest target if it's a range
                    price_target = float(matches[-1])
                    price_targets.append(price_target)
                    
            except (ValueError, IndexError):
                continue
        
        return statistics.median(price_targets) if price_targets else None
    
    def _find_ratings_table(self, soup: BeautifulSoup) -> Optional[Any]:
        """Find the table containing price target and rating columns"""
        tables = soup.find_all("table")
        
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if any("Price Target" in h for h in headers) and any("Rating" in h for h in headers):
                return table
        
        return None
