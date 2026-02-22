from sqlalchemy.engine.url import make_url

variants = [
    "postgresql://postgres:1@Something11@Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres",
    "postgresql://postgres:1%40Something11%40Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres",
    "postgresql://postgres:1\@Something11\@Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres",
]

for v in variants:
    try:
        url = make_url(v)
        print(f"URL: {v}")
        print(f"  User: {url.username}")
        print(f"  Password: {url.password}")
        print(f"  Host: {url.host}\n")
    except Exception as e:
        print(f"Failed: {v} -> {e}")

