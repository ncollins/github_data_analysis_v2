import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

c.execute("""
          CREATE TABLE IF NOT EXISTS users (
          name TEXT PRIMARY KEY,
          repos_url TEXT
          );
          """)

c.execute("""
          CREATE TABLE IF NOT EXISTS repos (
          name TEXT, 
          owner TEXT,
          url TEXT,
          language TEXT,
          PRIMARY KEY (name, owner)
          );
          """)

conn.commit()
