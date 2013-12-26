
import threading
import Queue

import requests

import login
import hacker_school

user_url = 'https://api.github.com/users/{}'

def get_page(url):
    try:
        #print url
        r = requests.get(url, auth=(login.username, login.password))
        #print r
        return r.json()
    except Exception as e:
        print('Error getting: {}'.format(url))
        return None


class FetchUser(threading.Thread):
    def __init__(self, queue):
          threading.Thread.__init__(self)
          self.queue = queue
          
    def run(self):
        while True:
            #grabs host from queue
            user = self.queue.get()
    
            print('Sending request for {0}'.format(user))
            data = get_page(user_url.format(user))
            try:
                print('Data recieved for {0}: {1}'.format(user, data['repos_url']))
            except:
                print('No repos_url for {0}'.format(user))
        
            #signals to queue job is done
            self.queue.task_done()


def main():
    queue = Queue.Queue()
    #spawn a pool of threads, and pass them queue instance 
    for i in range(10):
        t = FetchUser(queue)
        t.setDaemon(True)
        t.start()
              
    #populate queue with data   
    for host in hacker_school.groups['winter2013']:
        #url = user_url.format(host)
        #print url
        #print get_page(url)
        queue.put(host)
           
    #wait on the queue until everything has been processed     
    queue.join()
          
main()
