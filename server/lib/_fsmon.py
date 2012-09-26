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

import getpass

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
            line = self.fin.readline()
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
            "callback for filtering log lines by timestamp"
            m = props['re_time'].match(line)
            if not m:
                return False
            try:
                ts = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
            except ValueError as e:
                print 'no match'
                return false
            
            if ts > props['min_date']:
                return line
            else:
                return False
        
        "properties"
        str_min_ts = '2012-09-20 08:08:08,123'
    
        props={
            'filter_type':'ts',
            're_time' : re.compile('^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})'),
            'min_date' : datetime.datetime.strptime(str_min_ts, "%Y-%m-%d %H:%M:%S,%f")
        }
        
        for k in kwargs:
            props[k] = kwargs[k]
    
        if filter_type == 'ts':
            return log_ts_filter
        else:
            return None

class RainmakerEventHandler(FileSystemEventHandler):
    def __init__(self,  base_path):
        self.base_path = base_path
        self.callbacks = []

    """EventHandler"""
    def event_handler(self, event):
        for func in self.callbacks:
            func(event,self)

    def add_callback(self,func):
        self.callbacks.append(func)

    """ File System Events """
    def on_moved(self, event):
        self.event_handler(event)

    def on_created(self, event):
        self.event_handler(event)

    def on_deleted(self, event):
        self.event_handler(event)

    def on_modified(self, event):
		self.event_handler(event)
    
    """ Available Event properties """

    # return event file path relative to root
    def src_file_rel(self,event):
        return quote( event.src_path.replace(self.base_path+os.sep,'') )  

    def dest_file_rel(self,event):
        return quote( event.dest_path.replace(self.base_path+os.sep,'') )
     
    def event_type(self,event):
        return event.event_type


class Rainmaker():
   
    def __init__(self):
        self.event_handlers = {}
        self.observer = Observer()
        self.observer.start()

    def add_watch(self,watch_path,rec_flag=True):
        event_handler = RainmakerEventHandler( watch_path )
        self.event_handlers[watch_path] = event_handler
        self.observer.schedule( event_handler, watch_path, recursive = rec_flag) 
    
    def remove_watch(self, k): 
        eh = self.event_handlers.pop(k)
        self.observer.unschedule(eh)

    def shutdown(self):
        self.log.info( "Shutting down FSwatcher")
        self.observer.stop()
        self.observer.unschedule_all()
        self.observer.join()


