from src.database import Database
from src.analyzer import StockAnalyzer
import asyncio

async def main():
    try:
        db = Database()
        db.init_db()
        
        analyzer = StockAnalyzer()
        analysis = await analyzer.analyze("AAPL")
        
        from src.utils import save_analysis
        save_analysis(db, analysis)
        print("Success")
    except Exception as e:
        print(f"Exception Type: {type(e)}")
        print(f"Exception String: {str(e)}")

asyncio.run(main())
