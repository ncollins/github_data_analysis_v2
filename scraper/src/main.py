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

# threads

class FetchUrlWorker(threading.Thread):
    def __init__(self, input_queue, db_queue):
          threading.Thread.__init__(self)
          self.input_queue = input_queue
          
    def run(self):
        while True:
            _, user = self.input_queue.get() #grabs host from input_queue
            #print('Sending request for {0}'.format(user))
            data = get_page(user_url.format(user))
            try:
                db_queue.put(('users', (user, data.get('repos_url', None))))
                #print('Data recieved for {0}: {1}'.format(user, data.get('repos_url', None)))
            except:
                pass
                #print('Error getting {0}'.format(user))
            finally:
                self.input_queue.task_done() #signals to input_queue job is done


class DbWorker(threading.Thread):
    def __init__(self, queue):
        print('init db')
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        conn = sqlite3.connect('../../database.db')
        c = conn.cursor()
        while True:
            try:
                table, entry = self.queue.get()
                print('Got: {0}, {1}'.format(table, entry))
                if table == 'users':
                    c.execute('INSERT OR REPLACE INTO users values (?, ?)', entry)
                    conn.commit()
            except:
                print('Error with db insert: {0}'.format(entry))
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
        download_queue.put(('user', user))

    # start a DbWorker
    db_worker = DbWorker(db_queue)
    db_worker.setDaemon(True)
    db_worker.start()

    #wait on the queue until everything has been processed     
    download_queue.join()
    db_queue.join()
