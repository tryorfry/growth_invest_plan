from sqlalchemy.engine.url import make_url

url = make_url("postgresql://db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres")
print(url)
url = url.set(username="postgres", password="1@Something11@Anything1")
print(url.render_as_string(hide_password=False))
