import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

c.execute("""
          CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY,
          login TEXT,
          repos_url TEXT,
          avatar_url TEXT
          );
          """)

c.execute('CREATE UNIQUE INDEX users_login ON users (login);')

c.execute("""
          CREATE TABLE IF NOT EXISTS repos (
          id INTEGER PRIMARY KEY,
          user_id INTEGER,
          name TEXT KEY,
          url TEXT,
          language TEXT,
          fork INTEGER,
          contributors_url TEXT
          );
          """)
          
c.execute('CREATE INDEX repos_user_id ON repos (user_id);')
c.execute('CREATE INDEX repos_name ON repos (name);')

c.execute("""
          CREATE TABLE IF NOT EXISTS contributors (
          repo_id INTEGER,
          user_id INTEGER,
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
