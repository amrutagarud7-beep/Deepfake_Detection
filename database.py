import sqlite3

def create_database():
    # It's better to use the same DB file name your app expects
    # In your screenshot, I see 'users.db' in your folder, 
    # but your code says 'database.db'. Let's stick to 'database.db'.
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 1. Create Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # 2. Create History Table (This is what was missing!)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filetype TEXT,
        result TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database and tables created successfully!")