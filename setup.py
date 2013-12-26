import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

c.execute("""
          CREATE TABLE users (
          name TEXT PRIMARY KEY,
          repos_url TEXT
          );
          """)

conn.commit()
