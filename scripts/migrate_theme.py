import sqlite3

def migrate():
    conn = sqlite3.connect('stock_analysis.db')
    cursor = conn.cursor()
    
    try:
        print("Checking for theme_preference column in users table...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'theme_preference' not in columns:
            print("Adding theme_preference column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'dark'")
            conn.commit()
            print("Migration successful!")
        else:
            print("Column theme_preference already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
