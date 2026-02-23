import os
import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote_plus("1@Something11@Anything1")
url = f"postgresql://postgres.qvhphaxtfduvnylqfrno:{password}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(url)

migrations = [
    "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS user_id INTEGER NOT NULL DEFAULT 1;",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS user_id INTEGER NOT NULL DEFAULT 1;",
    "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS user_id INTEGER NOT NULL DEFAULT 1;"
]

with engine.begin() as conn:
    print("Executing ALTER TABLE migrations for Multi-Tenant RBAC...")
    for query in migrations:
        try:
            conn.execute(text(query))
            print(f"Success: {query}")
        except Exception as e:
            print(f"Error on {query}: {e}")

print("Tenant Migrations Complete.")
