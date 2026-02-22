from sqlalchemy import create_engine
import sys

db_url = "postgresql://postgres:1%40Something11%40Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

engine = create_engine(db_url)
print("Dialect: ", engine.dialect.name)

# We can intercept the connect args
try:
    cargs, cparams = engine.dialect.create_connect_args(engine.url)
    print("cargs:", cargs)
    print("cparams:", cparams)
except Exception as e:
    print("Failed to create connect args:", e)
