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
            # The new layout uses 'screener-view-table' or 'screener_table'
            table = soup.find('table', class_=lambda x: x and ('screener_table' in x or 'screener-view-table' in x))
            if not table:
                # Fallback: search for any styled-row if table class is obscured
                rows = soup.find_all('tr', class_=lambda x: x and 'styled-row' in x)
            else:
                # Primary row selector for new redesign
                rows = table.find_all('tr', class_=lambda x: x and ('screener-body-table-nw' in x or 'styled-row' in x))
            
            if not rows:
                return []

            tickers = []
            for row in rows[:count]:
                # NEW REDESIGN Strategy: Look for data-boxover-* attributes first
                # These are much more stable than column indices
                try:
                    ticker = None
                    company = None
                    mcap = None
                    
                    # Try to find a cell that has the data attributes
                    attr_cell = row.find(lambda tag: tag.has_attr('data-boxover-ticker'))
                    if attr_cell:
                        ticker = attr_cell.get('data-boxover-ticker')
                        company = attr_cell.get('data-boxover-company')
                        mcap = attr_cell.get('data-boxover-value')
                    
                    # Fallback to column indices if attributes not found
                    cols = row.find_all('td')
                    if len(cols) >= 10:
                        if not ticker: ticker = cols[1].get_text(strip=True)
                        if not company: company = cols[2].get_text(strip=True)
                        if not mcap: mcap = cols[6].get_text(strip=True)
                        price = cols[8].get_text(strip=True)
                        change = cols[9].get_text(strip=True)
                    else:
                        # Minimal fallback for very compact rows
                        ticker = ticker or row.find('a', class_='tab-link').get_text(strip=True)
                        price = "N/A"
                        change = "N/A"

                    if ticker:
                        tickers.append({
                            "ticker": ticker,
                            "company": company or "N/A",
                            "market_cap": mcap or "N/A",
                            "price": price if 'price' in locals() else "N/A",
                            "change": change if 'change' in locals() else "N/A"
                        })
                except Exception as row_e:
                    continue
            
            return tickers

        except Exception as e:
            print(f"Error scraping Finviz tickers for {sector_name}: {e}")
            return []
