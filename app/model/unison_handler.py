
# threaded shell execution
from subprocess import PIPE, Popen
from threading import Thread
import thread
import shlex
import os
from string import Template

# Excape path info from watchdog
from pipes import quote


# Queue imports for different python versions
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from watchdog.events import PatternMatchingEventHandler
from watchdog.events import FileSystemEvent

from lib import logger

class UnisonHandler(PatternMatchingEventHandler):
    def __init__(self,*args,**kwargs):
        super(PatternMatchingEventHandler,self).__init__(*args,**kwargs)
        self.log = logger.create(self.__class__.__name__)
        self.running = False
        self.event_q = Queue()
        self.attrs = {}
        self.funcs = {}
    
    # collect event(s)
    # take filename and subst for command
    # run command
    # process output looking for messages

    def on_any_event(self,event):
        self.log.debug(event.event_type)
        self.event_q.put( self.event_to_dict(event) ) 

    # event = FileSystemEvent('startup',self.profile['local_root'],True)
    def add_event(self,event_type,src_path,is_dir=False):
        event = FileSystemEvent(event_type,src_path,is_dir)
        self.on_any_event(event)

    def get_events(self):
        empty = False
        events = []
        while empty == False:
            try:
                events.append(self.event_q.get_nowait())
            except Empty:
                empty = True
        return events

    def process_events(self):
        events = self.get_events()
        cmd = self.build_cmds(events)
        if not cmd:
            return
        output = self.run_cmd(cmd)
        self.parse_output(output)
    
    def run_cmd(self,cmd):
        self.log.info('exec cmd: %s' % cmd)
        s_cmd = shlex.split(cmd) 
        p = Popen(s_cmd,stderr=PIPE, stdout=PIPE)
        result = {  'stdout':p.stdout.read(),
                    'stderr':p.stderr.read(),
                    'returncode':p.returncode,
                    'cmd':cmd
                 }
        self.log.debug('finished cmd: %s' % cmd)
        return result
        
    def parse_output(self,output):
        pass
    
    def event_to_dict(self,event):
        attrs = {}
        attrs['event_src_path'] = event.src_path  
        attrs['event_src_path_rel']=self.rel_path(self.attrs['local_root'],event.src_path)
        if hasattr(event,'dest_path'):
            attrs['event_dest_path'] = event.dest_path
            attrs['event_dest_path_rel'] = self.rel_path(self.attrs['local_root'],event.dest_path)
        attrs['event_type'] = event.event_type
        for k in attrs:
            attrs[k] = quote(attrs[k])
        return attrs

    def build_cmds(self,events):
        paths = []
        cmds = []
        # build commands
        for event in events:
            sub_opts = dict( 
                self.attrs.items() + 
                event.items()
            )
            cmd = Template(sub_opts[event['event_type']])
            cmds.append( cmd.safe_substitute(sub_opts) )
               
        return cmds

    # return event file path relative to root
    def rel_path(self,path_base,path2):
        return path2.replace(path_base+os.sep,'')
