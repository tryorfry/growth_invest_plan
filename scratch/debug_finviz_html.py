import sys
import os
import asyncio
from bs4 import BeautifulSoup

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.ticker_scraper import SectorTickerScraper

async def debug_html():
    scraper = SectorTickerScraper()
    sector = "Consumer Staples"
    slug = scraper.SECTOR_MAPPING.get(sector)
    url = f"https://finviz.com/screener.ashx?v=111&f={slug}&o=-marketcap"
    
    print(f"Fetching {url}...")
    response = scraper._get_response_sync(url)
    if not response:
        print("No response")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("\n--- TABLE CLASSES ---")
    tables = soup.find_all('table')
    for i, t in enumerate(tables[:10]):
        print(f"Table {i}: {t.get('class')}")
        
    print("\n--- ROW CLASSES ---")
    rows = soup.find_all('tr')
    classes = set()
    for r in rows:
        if r.get('class'):
            classes.add(" ".join(r.get('class')))
    for c in sorted(list(classes)):
        print(f"Row Class: {c}")

    # Check specifically for data-boxover
    print("\n--- DATA-BOXOVER COUNTS ---")
    tags = soup.find_all(lambda tag: tag.has_attr('data-boxover-ticker'))
    print(f"Found {len(tags)} tags with data-boxover-ticker")
    if tags:
        print(f"Sample Ticker: {tags[0].get('data-boxover-ticker')}")

if __name__ == "__main__":
    asyncio.run(debug_html())
