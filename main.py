
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

def get_finviz_data(ticker_symbol):
    """
    Scrapes Finviz for fundamental data.
    """
    url = f"https://finviz.com/quote.ashx?t={ticker_symbol}&p=d"
    
    try:
        response = requests.get(url, impersonate="chrome110", timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch Finviz data: {response.status_code}")
            return {}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        snapshot = soup.find("table", class_="snapshot-table2")
        
        if not snapshot:
            print("Finviz snapshot table not found.")
            return {}
            
        data = {}
        rows = snapshot.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            # Structure is Label | Value | Label | Value ...
            for i in range(0, len(cols), 2):
                if i+1 < len(cols):
                    key = cols[i].get_text(strip=True)
                    val = cols[i+1].get_text(strip=True)
                    data[key] = val
                    
        return data
    except Exception as e:
        print(f"Error fetching Finviz data: {e}")
        return {}

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
        print(f"Fetching historical data for {ticker_symbol}...")
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
            print(f"Fetching MarketBeat analyst ratings (post-earnings date: {last_earnings_date.date()})...")
            median_mbp = get_marketbeat_data(ticker_symbol, last_earnings_date)

        # Get Finviz Data
        print("Fetching Finviz fundamental data...")
        finviz_data = get_finviz_data(ticker_symbol)

        # Get Macrotrends Data (via yfinance for reliability)
        print("Fetching Financials (Revenue, EPS) via yfinance...")
        mt_data = {}
        try:
            # Financials (Quarterly often better for recent trends)
            q_fin = ticker.quarterly_financials
            if not q_fin.empty:
                latest_q = q_fin.iloc[:, 0]
                mt_data["Revenue"] = latest_q.get("Total Revenue", "N/A")
                mt_data["Operating Income"] = latest_q.get("Operating Income", "N/A")
                mt_data["Basic EPS"] = latest_q.get("Basic EPS", "N/A")
            
            # Next Earnings Warning
            next_earnings = None
            days_until_earnings = None
            
            # Try calendar first
            cal = ticker.calendar
            if cal and "Earnings Date" in cal:
                # Calendar returns a list of usually 2 dates (range)
                 dates = cal["Earnings Date"]
                 if dates:
                     next_earnings = dates[0] # Take the first one
            
            # Fallback to earnings_dates if calendar is empty
            if not next_earnings:
                ed = ticker.earnings_dates
                if ed is not None and not ed.empty:
                    now = pd.Timestamp.now(tz=ed.index.tz)
                    future = ed[ed.index > now].sort_index()
                    if not future.empty:
                        next_earnings = future.index[0]
            
            if next_earnings:
                # Ensure timezone awareness compatibility
                # Convert to Timestamp if it's a date object
                if not isinstance(next_earnings, pd.Timestamp):
                    next_earnings = pd.Timestamp(next_earnings)
                
                # Get current time with appropriate timezone
                if next_earnings.tz:
                    now = pd.Timestamp.now(tz=next_earnings.tz)
                else:
                    now = pd.Timestamp.now()
                    
                delta = next_earnings - now
                days_until_earnings = delta.days
                mt_data["Next Earnings"] = next_earnings
                mt_data["Days Until Earnings"] = days_until_earnings
        
        except Exception as e:
            print(f"Error fetching fundamental data (Macrotrends equivalent): {e}")



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
            "median_mbp": median_mbp,
            "finviz": finviz_data,
            "macrotrends": mt_data
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

        if data.get('finviz'):
            fv = data['finviz']
            print("\n--- Finviz Data ---")
            print(f"Market Cap: {fv.get('Market Cap', 'N/A')}")
            print(f"Analysts Recom: {fv.get('Recom', 'N/A')}")
            print(f"Inst Own: {fv.get('Inst Own', 'N/A')}")
            print(f"Avg Volume: {fv.get('Avg Volume', 'N/A')}")
            print(f"ROE: {fv.get('ROE', 'N/A')} | ROA: {fv.get('ROA', 'N/A')}")
            print(f"EPS Growth (This Y): {fv.get('EPS this Y', 'N/A')}")
            print(f"EPS Growth (Next Y): {fv.get('EPS next Y', 'N/A')}")
            print(f"EPS Growth (Next 5Y): {fv.get('EPS next 5Y', 'N/A')}")
            print(f"P/E: {fv.get('P/E', 'N/A')} | Fwd P/E: {fv.get('Forward P/E', 'N/A')} | PEG: {fv.get('PEG', 'N/A')}")

        if data.get('macrotrends'):
            mt = data['macrotrends']
            print("\n--- Fundamentals (Macrotrends Context) ---")
            
            # Format large numbers clearly
            def fmt_num(n):
                if isinstance(n, (int, float)):
                    if n >= 1e9: return f"${n/1e9:.2f}B"
                    if n >= 1e6: return f"${n/1e6:.2f}M"
                    return f"${n:,.2f}"
                return n

            print(f"Latest Revenue (Quarterly): {fmt_num(mt.get('Revenue', 'N/A'))}")
            print(f"Op Income (Quarterly): {fmt_num(mt.get('Operating Income', 'N/A'))}")
            print(f"Basic EPS (Quarterly): {mt.get('Basic EPS', 'N/A')}")
            
            if 'Next Earnings' in mt:
                days = mt.get('Days Until Earnings')
                date_str = mt['Next Earnings'].date()
                print(f"Next Earnings Date: {date_str} ({days} days left)")
                if days is not None and days < 10:
                     print("⚠️ WARNING: Earnings in less than 10 days! Trade with caution.")


