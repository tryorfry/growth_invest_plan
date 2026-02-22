import os
import asyncio
from src.database import Database
from src.analyzer import StockAnalyzer
from src.utils import save_analysis

os.environ["DATABASE_URL"] = "postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

async def main():
    try:
        db = Database()
        db.init_db()
        
        analyzer = StockAnalyzer()
        print("Fetching analysis...")
        analysis = await analyzer.analyze("AAPL")
        
        print("Attempting to save to Production DB...")
        save_analysis(db, analysis)
        print("Success")
    except Exception as e:
        import traceback
        print("--- TRACEBACK ---")
        traceback.print_exc()
        print("\n--- EXACT ERROR ---")
        print(f"Type: {type(e)}")
        print(f"Error: {str(e)}")

asyncio.run(main())
