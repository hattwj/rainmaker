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

#import copy
import collections

class RainmakerFlags():
    def subst(self,val):
        

# a collection to hold rainmakerdata classes
class RainmakerDataCollection(collections.MutableMapping):
    def __init__(self,data):
        self.data=data
        self.d={}
            
        for k in self.data:
            if self.data[k]['type']=='rainmaker_data':
                self.d[k]=RainmakerData(self.data[k])

    def __getitem__(self,key):
        return self.d[key]

    def __setitem__(self,key,value):
        if value.__class__.__name__==RainmakerData.__name__:
            self.d[key]=value.d
            self.data[key]=value.data
        else:
            print 'error'
            sys.exit()
    def __delitem__(self,key):
        del self.data[key]
        if key in self.d:
            del self.d[key]
    def __iter__(self):
        return iter(self.data)
    def __len__(self):
        return len(self.data)

# dict with keys - type,val,desc,default
class RainmakerData(collections.MutableMapping):
    def __init__(self,data=None):
        self.data=data or self.new_data()
        self.d={}
            
        for k in self.data['val']:
            if data['val'][k]['type']=='rainmaker_data':
                self.d[k]=RainmakerData(self.data['val'][k])

    def __getitem__(self,key):
        if key in self.d:
            return self.d[key]
        else:
            return self.data['val'][key]['val']

    def __setitem__(self,key,value):
        if value.__class__.__name__==self.__class__.__name__:
            self.d[key]=value.d
            self.data[key]=value.data
        else:
            if self.validate(self.data['val'][key],value):
                self.data['val'][key]['val']=value
    
    def new_data(self,val=None):
        return {'val':val,'type':'rainmaker_data','desc':None,'default':None,}

    def meta(self,key):
            return self.data['val'][key]

    def __delitem__(self,key):
        del self.data['val'][key]
        if key in self.d:
            del self.d[key]
    def __iter__(self):
        return iter(self.data['val'])
    def __len__(self):
        return len(self.data)

    def validate(self,q,val):
        if q['type']=='str':
            return len(str(val or ''))>0
        elif q['type']=='int':
            return 65536>=int(val)>0
        elif q['type']=='port':
            return 65536>=int(val)>0
        elif q['type']=='host':
            return len(str(val))>0
    
        elif q['type']=='localpath':
            return len(str(val))>0
    
        else:
            return False


#config class
class RainmakerConfig(dict):
    profiles = {}
    templates = {}
    profiles_data={}
    def __init__(self):
        
        self.home = os.path.expanduser('~')
        self.rain_dir = os.path.join(self.home,'.rainmaker')
        self.unison_dir = os.path.join(self.home,'.unison')
        self.profiles_f = 'profiles.yml'
        self.profiles_path=os.path.join(self.rain_dir,self.profiles_f)
        self.config_f = 'config.yml'
        self.config_path=os.path.join(self.rain_dir,self.config_f)
        self.app_dir = os.path.abspath(os.path.join(sys.path[0],'..'))
        self.app_conf_dir=os.path.join(self.app_dir,'conf')
        self.config_path_ro=os.path.join(self.app_dir,'conf',self.config_f)
               
        if not os.path.isdir(self.rain_dir):
            os.path.mkdir(self.rain_dir)
        if not os.path.isdir(self.unison_dir):
            os.path.mkdir(self.unison_dir)
        if not os.path.isfile(self.config_path):
            if not os.path.isfile(self.config_path_ro):
                print 'Unable to find config file'
                sys.exit()
            self.config_path=self.config_path_ro

        f = open(self.config_path,'r')
        self.config_data = yaml.safe_load( f )
        f.close()
                
        self.templates=RainmakerDataCollection(self.config_data['templates'])

        if os.path.isfile(self.profiles_path):
            f = open(self.profiles_path,'r')
            self.profiles_data = yaml.safe_load( f )
            f.close()

        if self.profiles_data == None:
            self.profiles_data={}
        
        self.profiles=RainmakerDataCollection(self.profiles_data)

    def __getitem__(self, key):
        val = self.config_data.__getitem__( key)
        return val

    def __setitem__(self, key, val):
        self.config_data.__setitem__( key, val)

    def save_profiles(self):
        print self.profiles_path
        f = open(self.profiles_path,'w')
        yaml.safe_dump(self.profiles_data, f)
        return f.close()

    def find(self,fname):
        paths=[
            self.rain_dir,
            self.unison_dir,
            self.app_dir,
            self.app_conf_dir
        ]

        for path in paths:
            result = os.path.join(path,fname)
            if os.path.isfile(result):
                return result
        return None

    def start(self, prf_f):
        return 'Not implemented'

    # Test config yaml file for misconfiguration and return results
    def test(self):
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
        self.config = W2Config()
        self.profiles = self.config.profiles

        self.msg_q = Queue()
        self.observer = Observer()
        self.observer.start()

        # If no profile just wait
        if profile:
            self.add_watch(profile)

    def add_watch(self,key):
        profile = self.profiles[key]

        log_levels = {
            'warn':logging.WARN,
            'info':logging.INFO,
            'debug':logging.DEBUG,
            False: logging.WARN 
        }

        # set up logging to file
        log_format = logging.format( '%(asctime)s %(name)-12s %(levelname)-8s %(message)s' ) 
        watch_logger = logging.getLogger(profile)
        watch_logger.setLevel( log_levels[ profile['log_level'] ] )
        watch_logger.setFormatter( log_format )

        logging.basicConfig(
            level   = log_levels[ profile['log_level'] ],
            format  = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt = '%H:%M:%S',
        )

        watch_logger.info( 'Loaded profile: ${profile}'.format(profile=profile) )

        event_handler = RainmakerEventHandler( self.config,profile, self.msg_q, watch_logger )
        self.event_handlers.append( event_handler )

        rec_flag = True
        if profile.has_key('recursive'):
            rec_flag = bool(profile['recursive']) 
        self.observer.schedule( event_handler, profile['root'], recursive = rec_flag) 
    
        if profile['cmds']['startup'] != '':
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
        profile = 'debug'

        if len(sys.argv)>1:
            profile = sys.argv[1]

        rain = Rainmaker(profile)
        
        while True:
            time.sleep(2)
            print  rain.messages()
 
    except KeyboardInterrupt:
        rain.shutdown()
