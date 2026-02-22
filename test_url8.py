from sqlalchemy.engine.url import make_url

db_url = "postgresql://postgres:1%40Something11%40Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

url = make_url(db_url)
print(url)
print(url.render_as_string(hide_password=False))
