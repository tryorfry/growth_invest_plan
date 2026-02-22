import urllib.parse

db_url = "postgresql://postgres:1@Something11@Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

print(f"Original: {db_url}")

if "://" in db_url:
    scheme, rest = db_url.split("://", 1)
    if "@" in rest:
        # We need to find the LAST '@' symbol which designates the host boundary
        # However, rsplit("@", 1) assumes the whole password contains '@'
        # What if the user already URL encoded part of it?
        
        # We should split on the FIRST '@' belonging to the host.
        # But wait, how do we distinguish? Usually, passwords don't have periods, and hosts do.
        # But rsplit is safer: anything before the last @ is the credentials.
        parts = rest.rsplit("@", 1)
        creds = parts[0]
        host_port_db = parts[1]
        
        if ":" in creds:
            user, pwd = creds.split(":", 1)
            # URL encode the entire password
            pwd = urllib.parse.unquote(pwd) # Unquote first to prevent double-encoding
            encoded_pwd = urllib.parse.quote(pwd)
            db_url = f"{scheme}://{user}:{encoded_pwd}@{host_port_db}"

print(f"Fixed:    {db_url}")
