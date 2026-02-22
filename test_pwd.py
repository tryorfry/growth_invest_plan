import psycopg2

try:
    conn = psycopg2.connect(
        host='db.qvhphaxtfduvnylqfrno.supabase.co', 
        dbname='postgres', 
        user='postgres', 
        password='1@Something11@Anything1', 
        port=5432,
        connect_timeout=2
    )
    print("Connected!")
except Exception as e:
    print(f"Error: {e}")
