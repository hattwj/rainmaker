import sys
import os
import time
import logging

# Execute Unison
from subprocess import PIPE, Popen
import shlex

# Excape path info from watchdog
from pipes import quote
# debug
from logging import INFO, basicConfig
# Watchdog
from watchdog.observers import Observer
#from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

class UnisonWatcher():
    def __init__(self,conf={}):
        # load defaults, empty string in events for full sync
        defaults = {
            'root_local': '/home/hattb/sync',
            'root_remote': '/home/rainmaker/users/hattb/sync',
            'ssh_key_path': '/home/hattb/.ssh/id_dsa',
            'unison_path': '/usr/bin/unison',
            'unison_prf': 'default1',
            'msg_queue': None,
            'events': {}
        }
        conf = dict(defaults.items()+conf.items() )
        self.q = Queue()
        self.roots = {}
        basicConfig(level   = logging.DEBUG,
                    format  = '%(asctime)s - %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S')
        self.observer = Observer()
        self.add(conf)
        self.observer.start()
        
    # Add a watch to a directory
    def add(self,root):
        self.roots[ root['root_local'] ] = {} #if self.roots.has_key(conf['root_local'])
        self.roots[ root['root_local'] ] = root
        # set default command for root
        self.roots[ root['root_local'] ]['cmd'] = root['unison_path']+' '+root['unison_prf']+' -ui text -sshargs "-i '+root['ssh_key_path']+'"'
        event_handler = UnisonEventHandler( root['root_local'], self.q )
        self.observer.schedule( event_handler, root['root_local'], recursive=True )
    
    # Stop all watches
    def stop(self):
        self.observer.stop()
        self.observer.unschedule_all()
        self.observer.join() 
        
    # Check for fs events and send
    # then return result set
    def update(self):
        event = 1
        while event:
            try:
                event = self.q.get_nowait() # or q.get(timeout=.1)
                self.collate(event)
            except Empty:
                event = None
        results = self.send()
        return results
    
    #Collate events and remove duplicates
    def collate(self,event):
        self.roots[event.root_local]['events'][event.path_relative] = event.event_type
    
    # add empty events to trigget full sync 
    def sync(self,rkey=None):
        if rkey and self.roots[rkey]:
            self.roots[rkey]['events']['']=''
        else:
            for root in self.roots:
                self.roots[root]['events']['']=''
        return self.update()

    # Send updates to server by calling unison    
    def send(self):
        results = []
        for rkey in self.roots.keys():
            root=self.roots[rkey]
            root_cmd = root['cmd']
            for path in root['events']:
                event_type = root['events'][path]
                # run commands to send files for unison
                cmd = root_cmd
                # if empty path sync everything
                if len(path)>0:
                    cmd += ' -path '+path
                cmd=shlex.split(cmd)

                #Done: Todo: Tokenize arguments -> http://docs.python.org/library/subprocess.html#subprocess.Popen
                p = Popen(cmd)#, shell=True)#, stdout=PIPE) 
                p.wait()
                results.append({
                    'cmd':cmd,
                    'path':path,
                    'root_local':root['root_local'],
                    'stdout': p.stdout,
                    'stderr': p.stderr,
                    'returncode': p.returncode,
                    'pid': p.pid
                })#,'event_type':event_type]})
        self.roots[rkey]['events']= {}
        return results
                
class UnisonEventHandler(FileSystemEventHandler):
    def __init__(self, root_local, q):
        self.q = q
        self.root_local = root_local

    """Custom EventHandler"""
    def catch_all_handler(self, event):
        #logging.debug( [self.root_local,event] )
        self.path_convert( event )
        self.q.put(event)
        
    def on_moved(self, event):
        self.catch_all_handler(event)

    def on_created(self, event):
        self.catch_all_handler(event)

    def on_deleted(self, event):
        self.catch_all_handler(event)

    def on_modified(self, event):
		self.catch_all_handler(event)
        
    def path_convert(self,event):
        event.path_relative = quote( event.src_path.replace(self.root_local+'/','') )
        event.root_local = self.root_local
    
if __name__ == "__main__":
    watcher = UnisonWatcher()
    watcher.sync()

    try:
        while True:
            time.sleep(2)
            result= watcher.update()
            if result:
                print result
    except KeyboardInterrupt:
        watcher.stop()
