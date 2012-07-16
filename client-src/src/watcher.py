#!/usr/bin/python
"""
This file is part of Rainmaker.

    Rainmaker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Rainmaker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Rainmaker.  If not, see <http://www.gnu.org/licenses/>.
"""
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

# Queue imports for different python versions
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

# Base config class, subclasses a dict for simple access
class W2Config(dict):
    def __init__(self,path = os.path.join('conf','w2.yml') ):
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

    def __init__(self,path = os.path.join('conf','w2conf.yml') ):
        self.path = path
        f = open(self.path,'r')
        
        config = yaml.safe_load( f )
        f.close()
        
        for key in config.iterkeys():
            self[key] = config[key]
            self[key]['name'] = key



    # Test config yaml file for misconfiguration and return results
    def testuconf_fail(self, path ):
         # return false if everything passed
         # return array of error codes on fail 
         pass
                
class RainmakerEventHandler(FileSystemEventHandler):
    def __init__(self, conf,uconf, msg_q, xlogger):
        self.cmd_q = Queue()
        self.threads_q = Queue()
        self.msg_q = msg_q
        self.conf = conf
        self.uconf = uconf.copy()
        self.log = xlogger

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
            #print cmd
            s_cmd = shlex.split(cmd) 
            p = Popen(s_cmd, stdout = PIPE, stderr=PIPE)
            result = {  'stdout':p.stdout.read(),
                        'stderr':p.stderr.read(),
                        'returncode':p.returncode,
                        'cmd':cmd
                     }
            self.msg_q.put( result )
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

class Rainmaker():
   
    def __init__(self, profile = None, conf_path = os.path.join('conf','w2conf.yml') ):

        self.event_handlers = []
        self.user_configs = W2UConfig(conf_path)
        self.config = W2Config()

        self.msg_q = Queue()
        self.observer = Observer()
        self.observer.start()

        # If no profile just wait
        if profile:
            self.add_watch(profile)

    def add_watch(self,profile):
        user_config = self.user_configs[profile]

        log_levels = {
            'warn':logging.WARN,
            'info':logging.INFO,
            'debug':logging.DEBUG,
            False: logging.WARN 
        }

        # set up logging to file
        log_format = logging.format( '%(asctime)s %(name)-12s %(levelname)-8s %(message)s' ) 
        watch_logger = logging.getLogger(profile)
        watch_logger.setLevel( log_levels[ user_config['log_level'] ] )
        watch_logger.setFormatter( log_format )

        logging.basicConfig(
            level   = log_levels[ user_config['log_level'] ],
            format  = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt = '%H:%M:%S',
        )

        watch_logger.info( 'Loaded profile: ${profile}'.format(profile=profile) )

        event_handler = RainmakerEventHandler( self.config,user_config, self.msg_q, watch_logger )
        self.event_handlers.append( event_handler )

        rec_flag = True
        if user_config.has_key('recursive'):
            rec_flag = bool(user_config['recursive']) 
        self.observer.schedule( event_handler, user_config['root'], recursive = rec_flag) 
    
        if user_config['cmds']['startup'] != '':
            event_handler.startup_cmd()

    def remove_watch(self, profile): 
        for eh in self.event_handlers:
            if eh['name'] == profile:
                self.observer.unschedule(eh)
                break 

    def messages(self):
        messages = []
        try:
            while True:
                messages.append( self.msg_q.get_nowait() )
        except Empty:
            pass

        return messages

    def shutdown(self):
        print "Shutting down FSwatcher"
        self.observer.stop()
        self.observer.unschedule_all()
        if self.event_handlers:
            self.observer.join()
        print "Shutting down thread and Fork pool"
        for idx, event_handler in enumerate( self.event_handlers ):
            event_handler.stop()

if __name__ == "__main__":

    try:
        profile = 'debug_profile'

        if len(sys.argv)>1:
            profile = sys.argv[1]

        rain = Rainmaker(profile)
        
        while True:
            time.sleep(2)
            print  rain.messages()
 
    except KeyboardInterrupt:
        rain.shutdown()
