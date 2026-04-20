import asyncio
import sys
from src.data_sources.macro_source import MacroSource

async def debug():
    print("Fetching Global Snapshot...")
    src = MacroSource()
    snapshot = await src.fetch_global_snapshot_async()
    print(f"Snapshot count: {len(snapshot)}")
    for item in snapshot:
        print(f" - {item['name']}: {item['value']} ({item['pct_change']:.2f}%)")

if __name__ == "__main__":
    asyncio.run(debug())
