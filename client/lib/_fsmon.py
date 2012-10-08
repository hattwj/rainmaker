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
import re
import datetime
import time
import logging
import yaml
import base64

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
from watchdog.events import FileSystemMovedEvent

# Queue imports for different python versions
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

#import copy

from _conf import RainmakerConfig
import _ssh

class Tail(object):
    "monitor a file for new lines"
    def __init__(self,fin):
        self.fin = fin
        self.running = False
        self.where = None


    def readlines_then_tail(self):
        "Iterate through lines and then tail for further lines."
        self.running = True
        while self.running==True:
            line = self.fin.readline()
            if line:
                line = self.filter(line)
                if line:
                    yield line
            else:
                self.tail()
     
    def tail(self,break_on_empty=False):
        "Listen for new lines added to file."
        while self.running==True:
            self.where = self.fin.tell()
            print 55
            line = self.fin.readline()
            print 66
            if not line:
                self.fin.seek(self.where)
                if break_on_empty:
                    break
                time.sleep(1)
            else:
                line = self.filter(line)
                if line:
                    yield line

    def filter(self,line):
        "replace this function to provide custom formatting"
        "returning False prevents the line from yielding"
        return line

    def new_lines(self):
        "yield newlines and return"
        self.running = True
        for line in self.tail(break_on_empty=True):
            yield line
    
    @staticmethod
    def get_log_filter(filter_type='ts',**kwargs):
        'returns function for filtering the file lines'
        
        def log_ts_filter(line):
            "func for filtering log lines by timestamp"
            m = props['re_line'].match(line)
            print line
            
            if not m:
                return False
            try:
                print m.groups()
                ts = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
            except ValueError as e:
                print 'no match'
                return false            
             
            if filter_type == 'groups':
                line = m.groups()

            if props['min_date'] is None:
                return line
            elif ts > props['min_date']:
                return line
            else:
                return False
        
        "properties"
        str_min_ts = '2012-09-20 08:08:08,123'
        p_ts = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})'
        p_ts += '\s+([a-zA-Z0-9]+)'
        p_ts += '\s+:\s+[a-zA-Z0-9]+\s+'
        p_ts += '\s+EVENT=([a-zA-Z0-9]+)'
        p_ts += '\s+SRC=([a-zA-Z0-9\+\/]+={0,3})'
        p_ts += '(?:\s+DEST=)?([a-zA-Z0-9\/\+]+={0,3})?'

        props={
            'filter_type':'ts',
            're_line' : re.compile("^%s" % p_ts ),
            'min_date' : datetime.datetime.strptime(str_min_ts, "%Y-%m-%d %H:%M:%S,%f")
        }
        
        for k in kwargs:
            props[k] = kwargs[k]

        return log_ts_filter


class RainmakerEventHandler(FileSystemEventHandler):

    def init2(self, conf, profile, msg_q, name):
        
        self.cmd_q = Queue()
        self.threads_q = Queue()
        self.msg_q = msg_q
        self.conf = conf
        self.profile = profile
        self.log = logging.getLogger('eh_%s' % name)
        self.name = name

        # Fill out nested macros (max 5 levels deep)
        for i in range(1,5):
            found_macro = False
            for flag in self.profile['cmd_macros']:
                new_macro = self.do_macro(self.profile['cmd_macros'][flag])
                if self.profile['cmd_macros'][flag] != new_macro:
                    found_macro = True
            if not found_macro:
                break

        # Add macros to commands
        for cmd_key,cmd_val in self.profile['cmds'].items():
            # process command list
            if isinstance(cmd_val, list): 
                for idx,item in enumerate(cmd_val):
                    self.profile['cmds'][cmd_key][idx]=self.do_macro(item)
            # process single command
            else:
                self.profile['cmds'][cmd_key] = self.do_macro(cmd_val)

        self.running = True
        self.start_threads()

    def start_threads(self):
        target = self.ssh_worker 
        for i in range( int(self.profile['max_threads']) ):
            t = Thread(target=target)
            t.daemon = True
            t.start()
            self.threads_q.put( t )
            target = self.cmd_worker

    # Listen on server for fs events
    def ssh_worker(self):
        
        opts={
            'port' : int(self.profile['port_menu']),
            'user' : self.profile['user'],
            'host' : self.profile['address'],
            'private_key' : self.profile['ssh_key_path']
        }
        
        ln_filter=Tail.get_log_filter('groups',min_date=None)
        
        c = _ssh.Client(**opts)
        
        c.connect()
        c.list()
        while self.running == True:
            time.sleep(1) 
            for line in c.new_lines():

                m = ln_filter(line)
                if not m:
                    continue
                                
                dest_path = None
                src_path = None
                event = None

                if len(m) >=4:
                    src_path = base64.standard_b64decode(m[3])
                    src_path = os.path.join(self.profile['local_root'],src_path)
                    event =FileSystemEvent(m[2], src_path ,True)

                if len(m) >=5 and not m[4] is None:
                    dest_path = base64.standard_b64decode(m[3])
                    dest_path = os.path.join(self.profile['local_root'],dest_path)
                    event =FileSystemMovedEvent(src_path, dest_path ,True)
                


                if not event is None: 
                    self.cmd_create(event)
        self.log.info( 'ssh_worker shutting down' )
        if c.running:
            c.close()

    # Thread to run command queue
    def cmd_worker(self):
        while self.running==True:
            try:
                cmd =  self.cmd_q.get_nowait()
            except Empty:
                time.sleep(1)
                continue
            self.log.info('exec cmd: %s' % cmd)
            s_cmd = shlex.split(cmd) 
            
            p = Popen(s_cmd, stdout = PIPE, stderr=PIPE)
            result = {  'stdout':p.stdout.read(),
                        'stderr':p.stderr.read(),
                        'returncode':p.returncode,
                        'cmd':cmd
                     }
            self.msg_q.put( result )
            self.log.debug('finished cmd: %s' % cmd)

    """EventHandler"""
    def cmd_create(self, event):
        self.log.debug('event fired: %s' % event.event_type)

        if event.src_path.endswith('.unison.tmp'):
            self.log.debug('Ignoring event: %s : %s' % (event.event_type, event.src_path))
            return

        #Start building command
        if self.profile['use_cmd_all'] and event.event_type != 'startup':
            cmd = self.profile['cmds']['all']
        else:
            cmd = self.profile['cmds'][event.event_type]
        
        # use base if none exists 
        if cmd == '' or cmd is None:
            self.log.debug( 'no command for event: %s' % event.event_type)
            return
        # process command list
        if isinstance(cmd, list): 
            for item in cmd:
                self.do_cmd(item,event)
        # process single command
        else:
            self.do_cmd(cmd,event)

    def do_cmd(self,cmd,event):       
        # Insert placeholder values
        cmd = self.profile.subst(cmd)
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
        for flag in self.profile['cmd_macros']:
            val = self.profile['cmd_macros'][flag]
            if cmd.find( flag ) != -1:
                cmd = cmd.replace( flag , val )
        return cmd
            
    """ Available client methods """
    def stop(self):
        self.log.info( 'stopping threads' )
        self.running = False
        while True:
            try:
                t =  self.threads_q.get_nowait()
                self.log.info('Stopping thread: %s' % t.name)
                t.join()
            except Empty:
                break
             
    def startup_cmd(self):
        event =FileSystemEvent('startup',self.profile['local_root'],True)
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
        return self.profile['local_root'] 
    
    def src_dir_full(self,event):
        return quote( event.src_path )

    # return event file path relative to root
    def src_file_rel(self,event):
        return event.src_path.replace(self.profile['local_root']+os.sep,'')  

    def dest_file_rel(self,event):
        return event.dest_path.replace(self.profile['local_root']+os.sep,'')  

    def event_type(self,event):
        return event.event_type

class Rainmaker():
   
    def __init__(self,config=None, auto_start=True ):
        self.log=logging.getLogger('main')
        self.event_handlers = []
        self.config = config if config else  RainmakerConfig()
        self.profiles = self.config.profiles

        self.msg_q = Queue()
        self.observer = Observer()
        self.observer.start()

        if not auto_start:
            return

        for k in self.profiles:
            if self.profiles[k]['auto_start']==True:
                self.add_watch(k)

        if not self.event_handlers:            
            self.log.warn('No running profiles')

    def add_watch(self,key):
        if not key in self.profiles:
            self.log.error('unknown profile %s' % key)

        self.log.info('Starting profile: %s' % key)
        profile = self.profiles[key]

        profile['local_root'] = os.path.abspath(os.path.expanduser(profile['local_root']))
        
        profile.subst_all()

        if not os.path.isdir(profile['local_root']):
            self.log.info('creating dir: %s' % profile['local_root'])
            os.mkdir(profile['local_root'])
        patterns=['*.unison.tmp']     
        event_handler = RainmakerEventHandler()
        event_handler.init2( self.config, profile, self.msg_q, key )
        self.event_handlers.append( event_handler )

        rec_flag = True
        if profile.has_key('recursive'):
            rec_flag = bool(profile['recursive']) 
        self.observer.schedule( event_handler, profile['local_root'], recursive = rec_flag) 
        
        logging.info('Started profile: %s' % key)
    
        if profile['cmds']['startup'] != '':
            event_handler.startup_cmd()

    def remove_watch(self, k): 
        for eh in self.event_handlers:
            if eh.name == k:
                self.log.info('Stopping profile: %s' % k)
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
        self.log.info( "Shutting down FSwatcher")
        self.observer.stop()
        self.observer.unschedule_all()
        self.observer.join()
        self.log.info("Shutting down thread and Fork pool")
        for eh in self.event_handlers:
            self.log.info('Stopping profile: %s' % eh.name)
            eh.stop()


