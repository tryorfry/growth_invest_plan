
from curl_cffi import requests
from bs4 import BeautifulSoup
import sys

# specific to windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

def test_marketbeat_access(ticker):
    url = f"https://www.marketbeat.com/stocks/NASDAQ/{ticker}/price-target/"
    
    try:
        print(f"Attempting to fetch {url} with curl_cffi...")
        # Impersonate Chrome 110
        response = requests.get(url, impersonate="chrome110", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Successfully fetched page.")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for ratings table
            tables = soup.find_all("table")
            print(f"Found {len(tables)} tables.")
            
            for i, table in enumerate(tables):
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                print(f"\nTable {i} Headers: {headers}")
                
                rows = table.find_all("tr")[:5]
                for row in rows:
                    cols = [td.get_text(separator=' ', strip=True) for td in row.find_all("td")]
                    if cols:
                        print(f"Row: {cols}")

        else:
            print("Failed to fetch.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter stock ticker symbol: ").upper()
    test_marketbeat_access(ticker)
