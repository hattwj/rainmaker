import sys
import os
import time
import logging
import yaml

# threaded shell execution
from subprocess import PIPE, Popen
from threading import Thread
import thread
import shlex

# Excape path info from watchdog
from pipes import quote

# debug
from logging import INFO, basicConfig
# Watchdog
from watchdog.observers import Observer
#from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileSystemEvent

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

# Base config class
class W2Config(dict):
    def __init__(self,path='w2.yml'):
        self.path = path
        
        f = open(self.path,'r')
        
        config = yaml.safe_load( f )
        f.close()

        for key in config.iterkeys():
            self[key] = config[key]
    

    # Test config yaml file for misconfiguration and return results
    def testconf_fail(self, path ):
         # return false if everything passed
         # return array of error codes on fail 
         pass

# User config class
class W2UConfig(dict):
    #profiles

    def __init__(self,path='w2conf.yml'):
        self.path = path
        f = open(self.path,'r')
        
        config = yaml.safe_load( f )
        f.close()
        
        for key in config.iterkeys():
            self[key] = config[key]


    # Test config yaml file for misconfiguration and return results
    def testuconf_fail(self, path ):
         # return false if everything passed
         # return array of error codes on fail 
         pass
    

                
class RainmakerEventHandler(FileSystemEventHandler):
    def __init__(self, uconf, cmd_q):
        self.cmd_q = cmd_q
        self.threads_q = Queue()
        self.msg_q = Queue()
        self.conf = W2Config()
        self.uconf = uconf.copy()

        # Fill out nested macros (max 5 levels deep)
        for i in range(1,5):
            found_macro = False
            for flag in self.uconf['cmd_macros']:
                new_macro = self.do_macro(self.uconf['cmd_macros'][flag])
                if self.uconf['cmd_macros'][flag] != new_macro:
                    found_macro = True
            if not found_macro:
                break

        # Add macros to commands
        for cmd_key,cmd_val in self.uconf['cmds'].items():
            # process command list
            if isinstance(cmd_val, list): 
                for idx,item in enumerate(cmd_val):
                    self.uconf['cmds'][cmd_key][idx]=self.do_macro(item)
            # process single command
            else:
                self.uconf['cmds'][cmd_key] = self.do_macro(cmd_val)

        self.running = True
        self.start_threads()

    def start_threads(self):
        for i in range( int(self.uconf['max_threads']) ):
            t = Thread(target=self.cmd_worker)
            t.daemon = True
            t.start()
            self.threads_q.put( t )
    # run
    def cmd_worker(self):
        while self.running==True:
            time.sleep(1)
            try:
                cmd =  self.cmd_q.get_nowait()
            except Empty:
                continue
            print cmd
            #cmd = shlex.split(cmd) 
            #p = Popen(cmd, stdout = PIPE, stderr=PIPE)
            #print p.stdout.read()
            #print p.stderr.read()
            #print p.returncode
        

    """EventHandler"""
    def cmd_create(self, event):
 
        #Start building command
        if self.uconf['use_cmd_all'] and event.event_type != 'startup':
            cmd = self.uconf['cmds']['all']
        else:
            cmd = self.uconf['cmds'][event.event_type]
        
        if cmd == '':
            cmd = self.uconf['cmds']['all']
        # process command list
        if isinstance(cmd, list): 
            for item in cmd:
                self.do_cmd(item,event)
        # process single command
        else:
            self.do_cmd(cmd,event)

    def do_cmd(self,cmd,event):       
        # Insert placeholder values
        for key in self.conf['cmd_flags']:
            flag = self.conf['cmd_flags'][key]
            if cmd.find( flag ) != -1:
                cmd = cmd.replace( flag , getattr(self, key )(event) )
        # Add command to command queue
        self.cmd_q.put(cmd)

    # scan a command for macros and substitute them
    def do_macro(self,cmd):
        if str(cmd) == '' or cmd is None:
            return ''
        for flag in self.uconf['cmd_macros']:
            val = self.uconf['cmd_macros'][flag]
            if cmd.find( flag ) != -1:
                cmd = cmd.replace( flag , val )
        return cmd
            

    """ Available client methods """
    def stop(self):
        self.running = False
        #self.threads_q.join()
             
    def startup_cmd(self):
        event =FileSystemEvent('startup',self.uconf['root'],True)
        self.cmd_create(event)

    """ File System Events """
    def on_moved(self, event):
        self.cmd_create(event)

    def on_created(self, event):
        self.cmd_create(event)

    def on_deleted(self, event):
        self.cmd_create(event)

    def on_modified(self, event):
		self.cmd_create(event)

    """ Available Event properties """
    def root(self,event):
        return self.uconf['root'] 

    def src_dir_rel(self,event):
        return '' 
    
    def src_dir_full(self,event):
        return quote( event.src_path )

    # return event file path relative to root
    def src_file_rel(self,event):
        return event.src_path.replace(self.uconf['root']+os.sep,'')  

    def src_file_full(self,event):
        return ''

    def src_file_name(self,event):
        return ''

    def src_file_type(self,event):
        return ''

    def dest_dir_rel(self,event):
        return ''

    def dest_dir_full(self,event):
        return ''

    def dest_file_rel(self,event):
        return event.dest_path.replace(self.uconf['root']+os.sep,'')  
    
    def dest_file_full(self,event):
        return ''
    
    def dest_file_name(self,event):
        return ''

    def dest_file_type(self,event):
        return ''
    
    def event_type(self,event):
        return event.event_type
    
 
if __name__ == "__main__":

    try:
        profile = 'default_profile'
        if len(sys.argv)>1:
            profile = sys.argv[1]
        
        user_config = W2UConfig('w2conf.yml')[profile]
        command_queue = Queue()
        observer = Observer() 
        basicConfig(level   = logging.DEBUG,
                    format  = '%(asctime)s - %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S')
        event_handler = RainmakerEventHandler( user_config, command_queue )
        rec_flag = True
        if user_config.has_key('recursive'):
            rec_flag = bool(user_config['recursive']) 
        observer.schedule( event_handler, user_config['root'], recursive = rec_flag) 
        observer.start()

        if user_config['cmds']['startup'] != '':
            event_handler.startup_cmd()

        while True:
            time.sleep(1)
                 
    except KeyboardInterrupt:
        print "Shutting down FSwatcher"
        observer.stop()
        observer.unschedule_all()
        observer.join()
        print "Shutting down thread and Fork pool" 
        event_handler.stop()
