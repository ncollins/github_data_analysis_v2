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

class FetchUser(threading.Thread):
    def __init__(self, input_queue, db_queue):
          threading.Thread.__init__(self)
          self.input_queue = input_queue
          
    def run(self):
        while True:
            user = self.input_queue.get() #grabs host from input_queue
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
                    c.execute('INSERT INTO users values (?, ?)', entry)
                    conn.commit()
            except:
                print('Error with db insert: {0}'.format(entry))
            finally:
                self.queue.task_done()
        conn.close()

# main

if __name__ == '__main__':
    user_queue = Queue.Queue()
    db_queue = Queue.Queue()

    #spawn a pool of threads, and pass them queue instance 
    fetch_user_workers = []
    for i in range(30):
        t = FetchUser(user_queue, db_queue)
        t.setDaemon(True)
        t.start()
        fetch_user_workers.append(t)
              
    #populate queue with data   
    for host in hacker_school.groups['winter2013']:
        user_queue.put(host)

    # start a DbWorker
    db_worker = DbWorker(db_queue)
    db_worker.setDaemon(True)
    db_worker.start()

    #wait on the queue until everything has been processed     
    user_queue.join()
    db_queue.join()
