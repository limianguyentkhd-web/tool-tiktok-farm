import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('farm_database.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', tables)
cursor.execute("SELECT * FROM farm_accounts LIMIT 10;")
print("=== FARM ACCOUNTS ===")
for r in cursor.fetchall():
    print(r)
