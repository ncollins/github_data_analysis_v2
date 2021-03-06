import time
import sqlite3
import threading
import queue
import argparse

import requests
import sqlalchemy

import login
import hacker_school

# setup / globals

user_url = 'https://api.github.com/users/{}'

# utility functions

def get_page(url):
    try:
        r = requests.get(url, auth=(login.username, login.password))
        return r.json()
    except Exception as e:
        print('Error getting: {}'.format(url))
        return None


def get_pages(url, max_pages=100):
    url = url + '?page={}'
    data = []
    for i in range(max_pages):
        print('GET: {}'.format(url.format(i)))
        ds = get_page(url.format(i))
        data.extend(ds)
        if len(ds) < 30:
            break
    return data


# threads

class FetchUrlWorker(threading.Thread):
    def __init__(self, download_queue, db_queue):
          threading.Thread.__init__(self)
          self.download_queue = download_queue
          self.db_queue = db_queue
          
    def run(self):
        while True:
            job = self.download_queue.get() #grabs host from download_queue
            try:
                page_type = job[0]
                if page_type == 'user':
                    url = job[1]
                    self._fetch_user(url)
                elif page_type == 'repos':
                    url, user_id = job[1:]
                    self._fetch_repos(url, user_id)
                elif page_type == 'contributors':
                    url, repo_id, user_id = job[1:]
                    self._fetch_contributors(url, repo_id, user_id)
                else:
                    print('Unrecognized page type "{0}".'.format(page_type))
            finally:
                self.download_queue.task_done() #signals to download_queue job is done

    def _fetch_user(self, url):
        data = get_page(url)
        try:
            user_id = data.get('id', None)
            login = data.get('login', None)
            repos_url = data.get('repos_url', None)
            avatar_url = data.get('avatar_url', None)
            if user_id:
                self.db_queue.put(('users', (user_id, login, repos_url, avatar_url)))
                if repos_url:
                    self.download_queue.put(('repos', repos_url, user_id))
            else:
                print('No "login" for {0}, data={1}'.format(url, data))
        except:
            print('problem with {0}'.format(login))

    def _fetch_repos(self, url, user_id):
        repos = get_pages(url)
        data = []
        for r in repos:
            data.append((r['id'],
                         user_id,
                         r['name'],
                         r['url'],
                         r['language'],
                         1 if r['fork'] == True else 0,
                         r['contributors_url']))
            if r['fork'] == False:
                self.download_queue.put(('contributors', r['contributors_url'], r['id'], user_id))
        if data:
            self.db_queue.put(('repos', data)) 

    def _fetch_contributors(self, url, repo_id, user_id):
        contributors = get_pages(url, max_pages = 30) # non-personal repos
        data = []
        for c in contributors:
            data.append((repo_id,
                         int(c['id']),
                         int(c['contributions'])))
        if data:
            self.db_queue.put(('contributors', data))

class DbWorker(threading.Thread):
    def __init__(self, queue, engine):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        conn = engine.connect()
        while True:
            table, data = self.queue.get()
            try:
                if table == 'users':
                    print('DB got: {0}, {1}'.format(table, data))
                    conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', data)
                elif table == 'repos':
                    print('DB got: {0}, [{1}, ...]'.format(table, data[0]))
                    conn.execute('INSERT OR REPLACE INTO repos VALUES (?, ?, ?, ?, ?, ?, ?)', data)
                elif table == 'contributors':
                    print('DB got: {0}, [{1}, ...]'.format(table, data[0]))
                    conn.execute('INSERT OR REPLACE INTO contributors VALUES (?, ?, ?)', data)
            except Exception as e:
                print('Error with db insert: table={0}, data={1}'.format(table, data))
            finally:
                self.queue.task_done()
        conn.close()

# main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sqlite')
    group.add_argument('--mysql')

    args = vars(parser.parse_args())

    print(args)

    for k, v in args.items():
        if k in ['mysql', 'sqlite'] and (v is not None):
            db, location = k, v
            break

    if db == 'sqlite':
        engine = sqlalchemy.create_engine('{0}:///{1}'.format(db, location))
    else:
        engine = sqlalchemy.create_engine('{0}://{1}'.format(db, location))

    connection = engine.connect()

    connection.close()

    download_queue = queue.Queue()
    db_queue = queue.Queue()

    #spawn a pool of threads, and pass them queue instance 
    fetch_url_workers = []
    for i in range(30):
        t = FetchUrlWorker(download_queue, db_queue)
        t.setDaemon(True)
        t.start()
        fetch_url_workers.append(t)
              
    #populate queue with data   
    for user in hacker_school.groups['winter2013']:
        download_queue.put(('user', user_url.format(user)))

    # start a DbWorker
    db_worker = DbWorker(db_queue, engine)
    db_worker.setDaemon(True)
    db_worker.start()

    #wait on the queue until everything has been processed     
    download_queue.join()
    db_queue.join()
