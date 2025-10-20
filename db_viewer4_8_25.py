import sqlite3
import pandas as pd

# Path to your SQLite DB
db_path = 'ONE_BIG_ACCOUNT_combined_data2025.db'

# Connect to the database
conn = sqlite3.connect(db_path)

# === 1. List all tables in the DB ===
def list_tables():
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    print("\n📋 Tables in the database:")
    print(tables)

# === 2. Preview contents of a specific table ===
def preview_table(table_name, n=10):
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {n};", conn)
        print(f"\n🔍 Preview of table '{table_name}':")
        print(df)
    except Exception as e:
        print(f"❌ Error reading table '{table_name}':", e)

# === Run it ===
if __name__ == "__main__":
    list_tables()
    
    # 👇 Preview any table by name here:
    preview_table("NEW_ONE_BIG_ACCOUNT_data_2025", n=15)

    # Close the connection
    conn.close()
