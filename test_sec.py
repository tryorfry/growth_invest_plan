import pandas as pd
import requests

try:
    headers = {'User-Agent': 'GrowthInvestPlan/1.0 (sachindangol@example.com)'}
    r = requests.get('https://www.sec.gov/files/company_tickers.json', headers=headers)
    data = r.json()
    tickers = [v['ticker'] for k,v in data.items()]
    print(f"Success! Got {len(tickers)} tickers.")
    print(f"Sample: {tickers[:5]}")
except Exception as e:
    print(f"Error: {e}")
