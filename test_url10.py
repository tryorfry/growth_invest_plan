from sqlalchemy.engine.url import URL
import urllib.parse

db_url = "postgresql://postgres:1%40Something11%40Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

# If the user put raw '@' symbols in the password without encoding them, 
# we need to manually extract the components so SQLAlchemy doesn't misparse the host
raw_url = db_url
if "://" in raw_url and "@" in raw_url:
    scheme_end = raw_url.find("://") + 3
    scheme = raw_url[:scheme_end - 3]
    rest = raw_url[scheme_end:]
    
    # The actual host block starts after the LAST @ symbol
    last_at = rest.rfind("@")
    if last_at != -1:
        creds = rest[:last_at]
        host_block = rest[last_at+1:]
        
        # Parse host block
        port = None
        db = None
        if "/" in host_block:
            host_port, db = host_block.split("/", 1)
        else:
            host_port = host_block
            
        if ":" in host_port:
            host, port_str = host_port.split(":", 1)
            if port_str.isdigit():
                port = int(port_str)
        else:
            host = host_port

        if ":" in creds:
            user, pwd = creds.split(":", 1)
            # We have all components separated safely!
            # Now build the SQL alchemy URL object natively via dictionary
            pwd_unquoted = urllib.parse.unquote(pwd)
            print(f"Driver: {scheme}")
            print(f"User: {user}")
            print(f"Pwd: {pwd_unquoted}")
            print(f"Host: {host}")
            print(f"Port: {port}")
            print(f"DB: {db}")
            
            final_url = URL.create(
                drivername=scheme,
                username=user,
                password=pwd_unquoted,
                host=host,
                port=port,
                database=db
            )
            print(f"Constructed: {final_url.render_as_string(hide_password=False)}")
