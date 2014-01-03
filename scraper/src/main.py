import time
import sqlite3
import threading
import Queue

import requests

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
        new_data = get_page(url.format(i))
        data.extend(new_data)
        if len(new_data) < 30:
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
            page_type, url = self.download_queue.get() #grabs host from download_queue
            if page_type == 'user':
                data = get_page(url)
                try:
                    login = data.get('login', None)
                    repos_url = data.get('repos_url', None)
                    if login:
                        self.db_queue.put(('users', (login, repos_url)))
                    else:
                        print('No "login" for {0}'.format(url))
                    if repos_url:
                        self.download_queue.put(('repos', repos_url))
                except:
                    print('problem with {0}'.format(login))
            elif page_type == 'repos':
                raw_data = get_pages(url)
                data = []
                for r in raw_data:
                    data.append((r['name'], # name
                                 r['owner']['login'], # owner
                                 r['url'],
                                 r['language'],
                                 1 if r['fork'] == True else 0,
                                 r['contributors_url']))
                if data:
                    self.db_queue.put(('repos', data))
                
            self.download_queue.task_done() #signals to download_queue job is done


class DbWorker(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        conn = sqlite3.connect('../../database.db')
        #c = conn.cursor()
        while True:
            table, data = self.queue.get()
            try:
                if table == 'users':
                    print('DB got: {0}, {1}'.format(table, data))
                    with conn:
                        conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', data)
                elif table == 'repos':
                    print('DB got: {0}, {1}'.format(table, data[0]))
                    with conn:
                        conn.executemany('INSERT OR REPLACE INTO repos VALUES (?, ?, ?, ?, ?, ?)', data)
            except:
                print('Error with db insert: table={0}, data={1}'.format(table, data))
            finally:
                self.queue.task_done()
        conn.close()

# main

if __name__ == '__main__':
    download_queue = Queue.Queue()
    db_queue = Queue.Queue()

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
    db_worker = DbWorker(db_queue)
    db_worker.setDaemon(True)
    db_worker.start()

    #wait on the queue until everything has been processed     
    download_queue.join()
    db_queue.join()
