import sqlite3
conn = sqlite3.connect(r'E:\AgroMind_Project_Structure\backend\agromind.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    print(t[0])
conn.close()