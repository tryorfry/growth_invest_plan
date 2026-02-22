import urllib.parse
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine

db_url = "postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

raw_url = db_url
if "://" in raw_url and "@" in raw_url:
    scheme_end = raw_url.find("://") + 3
    scheme = raw_url[:scheme_end - 3]
    rest = raw_url[scheme_end:]
    
    last_at = rest.rfind("@")
    creds = rest[:last_at]
    host_block = rest[last_at+1:]
    
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
        pwd_unquoted = urllib.parse.unquote(pwd)
        
        url_obj = URL.create(
            drivername=scheme,
            username=user,
            password=pwd_unquoted,
            host=host,
            port=port,
            database=db
        )
        print("Constructed URL:", url_obj.render_as_string(hide_password=False))
        
        # Test creation arguments
        engine = create_engine(url_obj)
        try:
            cargs, cparams = engine.dialect.create_connect_args(url_obj)
            print("cparams:", cparams)
        except Exception as e:
            print("cargs error:", e)

