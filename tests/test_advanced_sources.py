
import asyncio
from src.data_sources.options_source import OptionsSource
from src.data_sources.insider_source import InsiderSource
from src.data_sources.short_interest_source import ShortInterestSource

async def test_sources(ticker):
    print(f"Testing sources for {ticker}...")
    
    options_source = OptionsSource()
    insider_source = InsiderSource()
    short_source = ShortInterestSource()
    
    print("\n--- Testing OptionsSource ---")
    options_data = options_source.fetch_options_data(ticker)
    print(f"Options Data: {options_data}")
    
    print("\n--- Testing InsiderSource ---")
    insider_data = await insider_source.fetch_insider_data(ticker)
    print(f"Insider Data Keys: {insider_data.keys()}")
    if 'transactions' in insider_data:
        print(f"Recent Transactions Count: {len(insider_data['transactions'])}")
    
    print("\n--- Testing ShortInterestSource ---")
    short_data = short_source.fetch_short_interest(ticker)
    print(f"Short Data: {short_data}")

if __name__ == "__main__":
    asyncio.run(test_sources("AAPL"))
