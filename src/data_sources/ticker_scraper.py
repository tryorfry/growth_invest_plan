"""Scraper for fetching sector-specific ticker leaderboards from Finviz"""

import pandas as pd
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import streamlit as st
import json
import os
import time
from .base import DataSource

class SectorTickerScraper(DataSource):
    """Fetches top-performing or top-cap tickers for a specific sector"""
    # Benchmark cache path
    BENCHMARK_FILE = "data/sp500_benchmark.json"

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

    # --- EMERGENCY SAFETY NET ---
    # These hardcoded values are ONLY used as a last resort if BOTH:
    # 1. The live Finviz scan is blocked/down.
    # 2. The automatically updated Wikipedia benchmark cache (data/sp500_benchmark.json) is missing.
    # 
    # You DO NOT need to manually update this list; the system self-heals via Wikipedia weekly.
    SP500_GOLDEN_LIST = {
        "Technology": [
            ("AAPL", "Apple Inc."), ("MSFT", "Microsoft Corp."), ("NVDA", "NVIDIA Corp."), 
            ("AVGO", "Broadcom Inc."), ("ORCL", "Oracle Corp."), ("ADBE", "Adobe Inc."), 
            ("CRM", "Salesforce Inc."), ("AMD", "Advanced Micro Devices"), ("CSCO", "Cisco Systems"), 
            ("TXN", "Texas Instruments"), ("NOW", "ServiceNow Inc."), ("QCOM", "Qualcomm Inc."),
            ("INTC", "Intel Corp."), ("MU", "Micron Technology"), ("AMAT", "Applied Materials")
        ],
        "Healthcare": [
            ("LLY", "Eli Lilly & Co"), ("UNH", "UnitedHealth Group"), ("JNJ", "Johnson & Johnson"), 
            ("ABBV", "AbbVie Inc."), ("MRK", "Merck & Co."), ("TMO", "Thermo Fisher Scientific"), 
            ("DHR", "Danaher Corp."), ("AMGN", "Amgen Inc."), ("PFE", "Pfizer Inc."), 
            ("ISRG", "Intuitive Surgical"), ("ELV", "Elevance Health"), ("GILD", "Gilead Sciences"),
            ("BMY", "Bristol-Myers Squibb"), ("VRTX", "Vertex Pharma"), ("REGN", "Regeneron Pharma")
        ],
        "Financials": [
            ("JPM", "JPMorgan Chase"), ("V", "Visa Inc."), ("MA", "Mastercard Inc."), 
            ("BAC", "Bank of America"), ("WFC", "Wells Fargo"), ("BRK-B", "Berkshire Hathaway"), 
            ("GS", "Goldman Sachs"), ("MS", "Morgan Stanley"), ("SPGI", "S&P Global Inc."), 
            ("BLK", "BlackRock Inc."), ("AXP", "American Express"), ("C", "Citigroup Inc."),
            ("CB", "Chubb Limited"), ("PGR", "Progressive Corp"), ("BX", "Blackstone Inc")
        ],
        "Consumer Discretionary": [
            ("AMZN", "Amazon.com Inc."), ("TSLA", "Tesla Inc."), ("HD", "Home Depot"), 
            ("MCD", "McDonald's Corp."), ("NKE", "Nike Inc."), ("LOW", "Lowe's Companies"), 
            ("BKNG", "Booking Holdings"), ("SBUX", "Starbucks Corp."), ("TJX", "TJX Companies"), 
            ("CMG", "Chipotle Mexican Grill"), ("MAR", "Marriott International"), ("F", "Ford Motor Co."),
            ("GM", "General Motors"), ("ORLY", "O'Reilly Automotive"), ("LULU", "Lululemon Athletica")
        ],
        "Communication Services": [
            ("META", "Meta Platforms"), ("GOOGL", "Alphabet Inc. (Class A)"), ("GOOG", "Alphabet Inc. (Class C)"), 
            ("NFLX", "Netflix Inc."), ("DIS", "Walt Disney Co."), ("TMUS", "T-Mobile US"), 
            ("VZ", "Verizon Communications"), ("CMCSA", "Comcast Corp."), ("T", "AT&T Inc."), 
            ("EA", "Electronic Arts"), ("TTWO", "Take-Two Interactive"), ("WBD", "Warner Bros. Discovery"),
            ("CHTR", "Charter Communications"), ("FOXA", "Fox Corp"), ("LYV", "Live Nation")
        ],
        "Energy": [
            ("XOM", "Exxon Mobil Corp."), ("CVX", "Chevron Corp."), ("COP", "ConocoPhillips"), 
            ("SLB", "Schlumberger NV"), ("EOG", "EOG Resources"), ("MPC", "Marathon Petroleum"), 
            ("PSX", "Phillips 66"), ("VLO", "Valero Energy"), ("OXY", "Occidental Petroleum"), 
            ("HAL", "Halliburton Co."), ("BKR", "Baker Hughes"), ("DVN", "Devon Energy"),
            ("HES", "Hess Corp"), ("WMB", "Williams Companies"), ("KMI", "Kinder Morgan")
        ],
        "Industrials": [
            ("GE", "General Electric"), ("UNP", "Union Pacific"), ("CAT", "Caterpillar Inc."), 
            ("HON", "Honeywell International"), ("RTX", "RTX Corp."), ("UPS", "United Parcel Service"), 
            ("DE", "Deere & Co."), ("LMT", "Lockheed Martin"), ("BA", "Boeing Co."), 
            ("ADP", "Automatic Data Processing"), ("TDG", "TransDigm Group"), ("ETN", "Eaton Corp"),
            ("NSC", "Norfolk Southern"), ("CSX", "CSX Corp"), ("WM", "Waste Management")
        ],
        "Consumer Staples": [
            ("PG", "Procter & Gamble"), ("KO", "Coca-Cola Co."), ("PEP", "PepsiCo Inc."), 
            ("COST", "Costco Wholesale"), ("WMT", "Walmart Inc."), ("PM", "Philip Morris"), 
            ("EL", "Estee Lauder"), ("MO", "Altria Group"), ("MDLZ", "Mondelez Intl"), 
            ("CL", "Colgate-Palmolive"), ("GIS", "General Mills"), ("KMB", "Kimberly-Clark"),
            ("TGT", "Target Corp"), ("SYY", "Sysco Corp"), ("K", "Kellogg Co")
        ],
        "Utilities": [
            ("NEE", "NextEra Energy"), ("SO", "Southern Co."), ("DUK", "Duke Energy"), 
            ("SRE", "Sempra Energy"), ("AEP", "American Electric Power"), ("D", "Dominion Energy"), 
            ("EXC", "Exelon Corp."), ("PCG", "PG&E Corp."), ("PEG", "Public Service Enterprise"), 
            ("ED", "Consolidated Edison"), ("AEE", "Ameren Corp"), ("ES", "Eversource Energy"),
            ("WEC", "WEC Energy"), ("AWK", "American Water Works"), ("FE", "FirstEnergy")
        ],
        "Real Estate": [
            ("PLD", "Prologis Inc."), ("AMT", "American Tower"), ("EQIX", "Equinix Inc."), 
            ("CCI", "Crown Castle"), ("WY", "Weyerhaeuser Co."), ("PSA", "Public Storage"), 
            ("SBAC", "SBA Communications"), ("CBRE", "CBRE Group"), ("WELL", "Welltower Inc."), 
            ("DLR", "Digital Realty"), ("VICI", "VICI Properties"), ("O", "Realty Income"),
            ("AVB", "AvalonBay Communities"), ("EQR", "Equity Residential"), ("ARE", "Alexandria Real Estate")
        ],
        "Basic Materials": [
            ("LIN", "Linde plc"), ("SHW", "Sherwin-Williams"), ("FCX", "Freeport-McMoRan"), 
            ("APD", "Air Products & Chemicals"), ("NEM", "Newmont Corp."), ("CTVA", "Corteva Inc."), 
            ("ECL", "Ecolab Inc."), ("ALB", "Albemarle Corp."), ("NUE", "Nucor Corp."), 
            ("DOW", "Dow Inc."), ("VMC", "Vulcan Materials"), ("MLM", "Martin Marietta"),
            ("PPG", "PPG Industries"), ("DD", "DuPont de Nemours"), ("CE", "Celanese Corp")
        ]
    }

    def get_source_name(self) -> str:
        return "FinvizSectorScraper"

    async def fetch(self, sector_name: str, **kwargs) -> List[Dict[str, Any]]:
        """Asynchronous wrapper for scraping"""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.fetch_top_tickers, sector_name)

    @st.cache_data(ttl=14400) # Cache for 4 hours
    def fetch_top_tickers(_self, sector_name: str, count: int = 20, _cache_buster: float = 0) -> List[Dict[str, Any]]:
        """
        Scrapes Finviz for the top N tickers in a sector by Market Cap.
        Falls back to a verified S&P 500 leaderboard if scraping fails.
        """
        slug = _self.SECTOR_MAPPING.get(sector_name)
        if not slug:
            print(f"Unknown sector: {sector_name}")
            return []

        # v=111: Overview, f=sec_xxx: Sector Filter, o=-marketcap: Sort by Market Cap Desc
        url = f"https://finviz.com/screener.ashx?v=111&f={slug}&o=-marketcap"
        
        try:
            # Rotate User-Agents for better block resistance
            import random
            uas = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            headers = {
                "User-Agent": random.choice(uas),
                "Referer": "https://finviz.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            # Use the robust base class requester (handles impersonation)
            response = _self._get_response_sync(url, headers=headers)
            
            if not response or response.status_code != 200:
                return _self._get_fallback_list(sector_name)

            # Trigger a background refresh of the SP500 index once a week
            _self._maybe_refresh_index()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- BRUTE FORCE STRATEGY ---
            # Instead of looking for a specific table or row class, search for
            # any tag that has the 'data-boxover-ticker' attribute. 
            # This is the most resilient way to find tickers in the new layout.
            tickers = []
            seen_tickers = set()
            
            ticker_tags = soup.find_all(lambda tag: tag.has_attr('data-boxover-ticker'))
            
            for tag in ticker_tags:
                try:
                    ticker = tag.get('data-boxover-ticker')
                    if not ticker or ticker in seen_tickers:
                        continue
                    
                    # Extract associated data from the same tag's attributes
                    company = tag.get('data-boxover-company', "N/A")
                    mcap = tag.get('data-boxover-value', "N/A")
                    
                    # For Price and Change, we still want to look at the row if possible
                    # to get the latest values (though boxover-value might have some)
                    row = tag.find_parent('tr')
                    price = "N/A"
                    change = "N/A"
                    
                    if row:
                        cols = row.find_all('td')
                        if len(cols) >= 10:
                            # 8: Price, 9: Change in the standard v=111 layout
                            price = cols[8].get_text(strip=True)
                            change = cols[9].get_text(strip=True)
                        else:
                            # Fallback: look for spans with color-text (common in new layout)
                            price_span = row.find('span', class_=lambda x: x and 'color-text' in x)
                            if price_span: price = price_span.get_text(strip=True)

                    tickers.append({
                        "ticker": ticker,
                        "company": company,
                        "market_cap": mcap,
                        "price": price,
                        "change": change
                    })
                    seen_tickers.add(ticker)
                    
                    if len(tickers) >= count:
                        break
                except Exception:
                    continue
            
            return tickers

        except Exception as e:
            print(f"Error scraping Finviz tickers for {sector_name}: {e}")
            return _self._get_fallback_list(sector_name)

    def _get_fallback_list(self, sector_name: str) -> List[Dict[str, Any]]:
        """Provides a list of S&P 500 leaders. Prioritizes local JSON cache over hardcoded list."""
        # 1. Try to load from local JSON cache first
        local_data = self._load_benchmark_cache()
        leaders = local_data.get(sector_name)
        
        # 2. Fallback to hardcoded list if cache is empty or sector missing
        if not leaders:
            leaders = self.SP500_GOLDEN_LIST.get(sector_name, [])
        
        return [
            {
                "ticker": ticker,
                "company": company,
                "market_cap": "S&P 500 Benchmark",
                "price": "N/A",
                "change": "N/A",
                "is_fallback": True
            } for ticker, company in leaders
        ]

    def _maybe_refresh_index(self):
        """Checks if the S&P 500 index cache needs a refresh (every 7 days)"""
        try:
            os.makedirs("data", exist_ok=True)
            needs_update = True
            if os.path.exists(self.BENCHMARK_FILE):
                mtime = os.path.getmtime(self.BENCHMARK_FILE)
                if (time.time() - mtime) < 7 * 24 * 3600: # 7 days
                    needs_update = False
            
            if needs_update:
                st.info("🔄 Updating S&P 500 Benchmark Data from Wikipedia...")
                self._refresh_sp500_index()
        except Exception as e:
            print(f"Error checking benchmark cache: {e}")

    def _refresh_sp500_index(self):
        """Scrapes Wikipedia for the latest S&P 500 GICS sector constituents"""
        wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        try:
            resp = self._get_response_sync(wiki_url)
            if not resp or resp.status_code != 200:
                return
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            if not table:
                return
            
            new_data = {}
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    ticker = cols[0].text.strip().replace('.', '-')
                    company = cols[1].text.strip()
                    sector = cols[3].text.strip()
                    
                    if sector not in new_data:
                        new_data[sector] = []
                    new_data[sector].append((ticker, company))
            
            if new_data:
                with open(self.BENCHMARK_FILE, 'w') as f:
                    json.dump(new_data, f)
        except Exception as e:
            print(f"Error refreshing S&P 500 index: {e}")

    def _load_benchmark_cache(self) -> Dict[str, Any]:
        """Loads the S&P 500 benchmark data from local storage"""
        if os.path.exists(self.BENCHMARK_FILE):
            try:
                with open(self.BENCHMARK_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

class DynamicScreener(DataSource):
    """Fetches high conviction reversal/momentum candidates from Finviz"""
    
    def get_source_name(self) -> str:
        return "FinvizDynamicScreener"
        
    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """Asynchronous wrapper for scraping"""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.fetch_top_candidates)
        
    @st.cache_data(ttl=14400) # Cache for 4 hours
    def fetch_top_candidates(_self, count: int = 30, _cache_buster: float = 0) -> List[Dict[str, Any]]:
        """
        Scrapes Finviz for top reversal candidates.
        Criteria: Mid Cap+, Rel Vol > 1.5, Price showing bullish momentum shift.
        """
        # v=111: Overview, o=-volume: Sort by Volume Desc
        url = "https://finviz.com/screener.ashx?v=111&f=cap_midover,sh_relvol_o1.5,ta_sma50_pa&o=-volume"
        
        try:
            import random
            from bs4 import BeautifulSoup
            uas = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            headers = {
                "User-Agent": random.choice(uas),
                "Referer": "https://finviz.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            response = _self._get_response_sync(url, headers=headers)
            
            if not response or response.status_code != 200:
                print(f"Finviz dynamic screener failed with status code {response.status_code if response else 'None'}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            
            tickers = []
            seen_tickers = set()
            
            ticker_tags = soup.find_all(lambda tag: tag.has_attr('data-boxover-ticker'))
            
            for tag in ticker_tags:
                try:
                    ticker = tag.get('data-boxover-ticker')
                    if not ticker or ticker in seen_tickers:
                        continue
                    
                    company = tag.get('data-boxover-company', "N/A")
                    
                    tickers.append({
                        "ticker": ticker,
                        "company": company
                    })
                    seen_tickers.add(ticker)
                    
                    if len(tickers) >= count:
                        break
                except Exception:
                    continue
            
            return tickers

        except Exception as e:
            print(f"Error scraping Finviz dynamic screener: {e}")
            return []
