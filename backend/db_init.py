import sqlite3, os
BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, "expenses.db")
conn = sqlite3.connect(DB)
c = conn.cursor()
c.executescript('''
CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL, title TEXT, amount REAL NOT NULL, payer_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS splits (id INTEGER PRIMARY KEY AUTOINCREMENT, expense_id INTEGER NOT NULL, member_id INTEGER NOT NULL, share REAL NOT NULL);
''')
conn.commit()
conn.close()
print("Initialized DB at", DB)
