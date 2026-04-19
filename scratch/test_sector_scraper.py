"""Diagnostic script for SectorTickerScraper"""
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.ticker_scraper import SectorTickerScraper

async def test_scraper():
    scraper = SectorTickerScraper()
    sector = "Consumer Staples"
    print(f"Testing scraper for sector: {sector}")
    
    # Use the internal _get_response_sync to see what's happening
    slug = scraper.SECTOR_MAPPING.get(sector)
    url = f"https://finviz.com/screener.ashx?v=111&f={slug}&o=-marketcap"
    print(f"URL: {url}")
    
    response = scraper._get_response_sync(url)
    if not response:
        print("FAILED: No response received.")
        return
        
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"FAILED: Status {response.status_code}")
        print(response.text[:500])
        return
        
    # Check for table
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='screener_table')
    if table:
        print("SUCCESS: Found screener_table")
        rows = table.find_all('tr', class_=lambda x: x and 'screener-body-table-nw' in x)
        print(f"Found {len(rows)} matching rows.")
        if rows:
            cols = rows[0].find_all('td')
            if len(cols) > 1:
                print(f"First ticker sample: {cols[1].get_text(strip=True)}")
    else:
        print("FAILED: screener_table not found in HTML.")
        # Print a snippet of where the table should be or of the whole body
        print("HTML Snippet (first 1000 chars):")
        print(response.text[:1000])

if __name__ == "__main__":
    asyncio.run(test_scraper())
