import os
import asyncio
from sqlalchemy import text
from src.database import Database

os.environ["DATABASE_URL"] = "postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

async def main():
    try:
        db = Database()
        db.init_db()
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE analyses ALTER COLUMN shares_outstanding TYPE BIGINT;"))
            conn.commit()
        print("Column altered successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
