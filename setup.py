import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

c.execute("""
          CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY,
          login TEXT KEY,
          repos_url TEXT
          );
          """)

c.execute("""
          CREATE TABLE IF NOT EXISTS repos (
          id INTEGER PRIMARY KEY,
          user_id INTEGER KEY,
          name TEXT KEY,
          url TEXT,
          language TEXT,
          fork INTEGER,
          contributors_url TEXT
          );
          """)

c.execute("""
          CREATE TABLE IF NOT EXISTS contributors (
          repo_id INTEGER KEY,
          user_id INTEGER KEY,
          contributions INTEGER,
          PRIMARY KEY (repo_id, user_id)
          );
          """)

c.execute("""
          CREATE VIEW IF NOT EXISTS repos_with_owner
          AS
          SELECT
          repos.id AS repo_id, repos.name AS repo_name,
          users.id as repo_owner_id, users.login as repo_owner_login
          FROM repos LEFT JOIN users ON repos.user_id = users.id;
          """)

conn.commit()
