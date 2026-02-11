
import yfinance as yf
import pandas as pd
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import statistics
import re

# specific to windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

def get_marketbeat_data(ticker_symbol, last_earnings_date):
    """
    Scrapes MarketBeat for analyst ratings and calculates median MBP.
    """
    # Try NASDAQ first, then NYSE (generic fallback list could be improved)
    exchanges = ["NASDAQ", "NYSE"]
    
    for exchange in exchanges:
        url = f"https://www.marketbeat.com/stocks/{exchange}/{ticker_symbol}/price-target/"
        try:
            # Impersonate Chrome to bypass protection
            response = requests.get(url, impersonate="chrome110", timeout=10)
            if response.status_code == 200:
                print(f"Successfully fetched MarketBeat data from {url}")
                return parse_marketbeat_data(response.content, last_earnings_date)
            elif response.status_code == 404:
                continue # Try next exchange
        except Exception as e:
            print(f"Bypassing MarketBeat check due to error: {e}")
            return None
            
    print(f"Could not find MarketBeat page for {ticker_symbol}")
    return None

def parse_marketbeat_data(html_content, last_earnings_date):
    soup = BeautifulSoup(html_content, 'html.parser')
    price_targets = []
    
    # improved implementation to find the correct table
    tables = soup.find_all("table")
    rating_table = None
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if any("Price Target" in h for h in headers) and any("Rating" in h for h in headers):
            rating_table = table
            break
            
    if not rating_table:
        return None

    # Parse rows
    rows = rating_table.find_all("tr")
    
    count = 0 
    for row in rows:
        cols = row.find_all("td")
        if not cols:
            continue
            
        # Structure varies, but usually: Date, Brokerage, Analyst, Action, Rating, Price Target, ...
        # layout uses 8 columns based on investigation
        if len(cols) < 6:
            continue

        try:
            date_str = cols[0].get_text(strip=True)
            # MarketBeat dates are usually MM/DD/YYYY
            rating_date = datetime.strptime(date_str, "%m/%d/%Y").astimezone(last_earnings_date.tzinfo)
            
            if rating_date < last_earnings_date:
                continue # Skip old ratings

            price_target_str = cols[5].get_text(strip=True)
            # Handle formats like "$300.00" or "$300.00 -> $320.00" or ""
            if not price_target_str:
                continue
                
            # Extract numbers
            matches = re.findall(r'\$?(\d+\.\d{2})', price_target_str)
            if matches:
                 # If range ($300 -> $320), take the new target (last one)
                price_target = float(matches[-1]) 
                price_targets.append(price_target)
                count += 1
                
        except ValueError:
            continue
            
    if price_targets:
        return statistics.median(price_targets)
    return None

def get_stock_data(ticker_symbol):
    """
    Fetches stock data and calculates ATR, EMAs.
    
    Args:
        ticker_symbol (str): The stock ticker symbol.
        
    Returns:
        dict: A dictionary containing the latest metrics.
    """
    try:
        # Fetch historical data - need enough for EMA200
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="2y")

        if hist.empty:
            print(f"Error: No data found for ticker symbol '{ticker_symbol}'.")
            return None

        # Earnings Dates
        earnings = ticker.earnings_dates
        last_earnings_date = None
        if earnings is not None and not earnings.empty:
            # Filter for past dates
            now = pd.Timestamp.now(tz=earnings.index.tz)
            past_earnings = earnings[earnings.index < now]
            if not past_earnings.empty:
                last_earnings_date = past_earnings.index[0]

        # Get MarketBeat Data
        median_mbp = None
        if last_earnings_date:
            median_mbp = get_marketbeat_data(ticker_symbol, last_earnings_date)

        # Calculate True Range (TR) & ATR
        high_low = hist['High'] - hist['Low']
        high_close = (hist['High'] - hist['Close'].shift()).abs()
        low_close = (hist['Low'] - hist['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # ATR 14
        atr = true_range.ewm(span=14, adjust=False).mean()

        # Calculate EMAs
        ema20 = hist['Close'].ewm(span=20, adjust=False).mean()
        ema50 = hist['Close'].ewm(span=50, adjust=False).mean()
        ema200 = hist['Close'].ewm(span=200, adjust=False).mean()

        # Get latest data
        latest = hist.iloc[-1]
        latest_date = hist.index[-1]
        
        return {
            "atr": atr.iloc[-1],
            "ema20": ema20.iloc[-1],
            "ema50": ema50.iloc[-1],
            "ema200": ema200.iloc[-1],
            "open": latest['Open'],
            "high": latest['High'],
            "low": latest['Low'],
            "close": latest['Close'],
            "current_price": latest['Close'], # yfinance history 'Close' is the latest price
            "timestamp": latest_date,
            "earnings_date": last_earnings_date,
            "median_mbp": median_mbp
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter stock ticker symbol: ").upper()
    
    data = get_stock_data(ticker)
    
    if data:
        print(f"\n--- Analysis for {ticker} ({data['timestamp']}) ---")
        print(f"Current Price: {data['current_price']:.2f}")
        print(f"Open: {data['open']:.2f} | High: {data['high']:.2f} | Low: {data['low']:.2f} | Close: {data['close']:.2f}")
        print("-" * 30)
        print(f"ATR (14):   {data['atr']:.2f}")
        print(f"EMA 20:     {data['ema20']:.2f}")
        print(f"EMA 50:     {data['ema50']:.2f}")
        print(f"EMA 200:    {data['ema200']:.2f}")
        
        if data.get('earnings_date'):
            print(f"Last Earnings: {data['earnings_date'].date()}")
        
        if data.get('median_mbp'):
            print(f"Median MBP (Post-Earnings): ${data['median_mbp']:.2f}")

