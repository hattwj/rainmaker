import sys
import os
import time
import logging
import yaml

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

class ConfigLoader():
    # load defaults, empty string in events for full sync
    """ defaults = {
        'unison_watcher' : {
            'root_local': '/home/hattb/sync',
            'root_remote': '/home/rainmaker/users/hattb/sync',
            'ssh_key_path': '/home/hattb/.ssh/id_dsa',
            'unison_path': '/usr/bin/unison',
            'unison_prf': 'default1',
            'msg_queue': None,
            'events': {}
        },
        'gui' : {
        }
    }
        
    """
    path = 'rainconf.yaml'

    def default(self,key=None):
        f = open(self.path,'r')
        
        config = yaml.safe_load( f )
        f.close()
        if key:
            return config[key]
        return config    

    def __init__(self):
    
        # find current directory of application
        # or .rainmaker directory and load config
        # or load path if passed
        # load from .rainmaker if just a filename is sent
        # merge that yaml file with defaults
        pass
    
    # Test config yaml file for misconfiguration and return results
    def testconf_fail(self, path ):
         # return false if everything passed
         # return array of error codes on fail 
         pass

    

class UnisonWatcher():
    def __init__(self,conf):
        self.q = Queue()
        self.roots = {}
        basicConfig(level   = logging.DEBUG,
                    format  = '%(asctime)s - %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S')
        self.observer = Observer()
        self.add(conf)
        self.observer.start()
        
    # Add a watch to a directory
    def add(self,config):
        print repr(config)
        self.roots[ config['root_local'] ] = {} #if self.roots.has_key(conf['root_local'])
        self.roots[ config['root_local'] ] = config
        # set default command for root
        self.roots[ config['root_local'] ]['cmd'] = config['unison_path']+' '+config['unison_prf']+' -ui text -sshargs "-i '+config['ssh_key_path']+'"'
        event_handler = UnisonEventHandler( config['root_local'], self.q )
        self.observer.schedule( event_handler, config['root_local'], recursive=True )
    
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
        
        # sync only this one host
        if rkey and self.roots[rkey]:
            self.roots[rkey]['events']['']=''
        else:
            # sync all unison hosts
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
                print cmd
                # (by removing the -path flag we are telling unison to do a full sync)
                if len(path)>0:
                    cmd += ' -path '+path
                cmd=shlex.split(cmd)

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
                })
        self.roots[rkey]['events']= {}
        return results
                
class UnisonEventHandler(FileSystemEventHandler):
    def __init__(self, root_local, q):
        self.q = q
        self.root_local = root_local

    """Custom EventHandler"""
    def catch_all_handler(self, event):
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
    # load config
    cl = ConfigLoader()
    conf = cl.default('rainmaker')    

    # create watcher
    watcher = UnisonWatcher(conf)

    # start initial sync with server 
    watcher.sync()

    try:
        while True:
            time.sleep(2)
            result= watcher.update()
            if result:
                print result
    except KeyboardInterrupt:
        watcher.stop()
