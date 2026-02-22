from sqlalchemy.engine.url import make_url

db_url = "postgresql://postgres:1%40Something11%40Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"
try:
    url = make_url(db_url)
    print("make_url SUCCESS")
    print(f"User: {url.username}")
    print(f"Password: {url.password}")
    print(f"Host: {url.host}")
except Exception as e:
    print(f"make_url FAILED: {e}")
