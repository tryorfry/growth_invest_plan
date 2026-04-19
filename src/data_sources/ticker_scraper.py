"""Scraper for fetching sector-specific ticker leaderboards from Finviz"""

import pandas as pd
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import streamlit as st
from .base import DataSource

class SectorTickerScraper(DataSource):
    """Fetches top-performing or top-cap tickers for a specific sector"""
    
    SECTOR_MAPPING = {
        "Technology": "sec_technology",
        "Healthcare": "sec_healthcare",
        "Financials": "sec_financial",
        "Consumer Discretionary": "sec_consumercyclical",
        "Communication Services": "sec_communicationservices",
        "Industrials": "sec_industrials",
        "Consumer Staples": "sec_consumerdefensive",
        "Energy": "sec_energy",
        "Utilities": "sec_utilities",
        "Real Estate": "sec_realestate",
        "Basic Materials": "sec_basicmaterials"
    }

    def get_source_name(self) -> str:
        return "FinvizSectorScraper"

    async def fetch(self, sector_name: str, **kwargs) -> List[Dict[str, Any]]:
        """Asynchronous wrapper for scraping"""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.fetch_top_tickers, sector_name)

    @st.cache_data(ttl=14400) # Cache for 4 hours
    def fetch_top_tickers(_self, sector_name: str, count: int = 20) -> List[Dict[str, Any]]:
        """
        Scrapes Finviz for the top N tickers in a sector by Market Cap.
        """
        slug = _self.SECTOR_MAPPING.get(sector_name)
        if not slug:
            print(f"Unknown sector: {sector_name}")
            return []

        # v=111: Overview, f=sec_xxx: Sector Filter, o=-marketcap: Sort by Market Cap Desc
        url = f"https://finviz.com/screener.ashx?v=111&f={slug}&o=-marketcap"
        
        try:
            # Use the robust base class requester (handles impersonation)
            response = _self._get_response_sync(url)
            if not response or response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            # Finviz table rows for tickers usually have class 'screener-body-table-nw'
            # Or they are inside a table with class 'screener_table'
            table = soup.find('table', class_='screener_table')
            if not table:
                return []

            tickers = []
            rows = table.find_all('tr', class_=lambda x: x and 'screener-body-table-nw' in x)
            
            for row in rows[:count]:
                cols = row.find_all('td')
                if len(cols) < 10: continue
                
                # Column mapping for v=111 Overview:
                # 0: No, 1: Ticker, 2: Company, 3: Sector, 4: Industry, 5: Country, 6: Market Cap, 7: P/E, 8: Price, 9: Change, 10: Volume
                try:
                    ticker = cols[1].get_text(strip=True)
                    company = cols[2].get_text(strip=True)
                    market_cap = cols[6].get_text(strip=True)
                    price = cols[8].get_text(strip=True)
                    change = cols[9].get_text(strip=True)
                    
                    tickers.append({
                        "ticker": ticker,
                        "company": company,
                        "market_cap": market_cap,
                        "price": price,
                        "change": change
                    })
                except Exception as row_e:
                    continue
            
            return tickers

        except Exception as e:
            print(f"Error scraping Finviz tickers for {sector_name}: {e}")
            return []
