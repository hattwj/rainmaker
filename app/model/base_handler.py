from os import sep
# Queue imports for different python versions
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from watchdog.events import PatternMatchingEventHandler
from watchdog.events import FileSystemMovedEvent
from watchdog.events import FileSystemEvent

class BaseHandler(PatternMatchingEventHandler):
    def __init__(self,*args,**kwargs):
        PatternMatchingEventHandler.__init__(self,*args,**kwargs)
        self.event_q = Queue()
    
    ## handler - universal
    # belongs to profile
    # ignore patterns (from profile)
    # collect event(s)
    # store until requested
    
    ## profile - unique attrs/generic class
    # pluggable with attrs
    # take filename and subst for command
    # run command
    # process output looking for messages / errors
    # validations, questions through config
    # attrs that can call functions or unique classes

    ## log analyzer - universal with callbacks
    # log messages/errors
    # forward information to 
    # - gui?
    # - desktop notifications
    
    ## store events in queue
    def on_any_event(self,event):
        self.event_q.put( event ) 
    
    ## Add event to queue
    # event = FileSystemEvent('startup',self.profile['local_root'],True)
    def add_event(self,event_type,src_path,is_dir=False,dest_path=None):
        if event_type == 'moved':
            event = FileSystemMovedEvent(src_path,dest_path,is_dir)
        else:
            event = FileSystemEvent(event_type,src_path,is_dir)
        self.dispatch(event)
    
    ## return array of events
    def get_events(self,path):
        events = []
        while True:
            try:
                event = self.event_to_dict( self.event_q.get_nowait(),path) 
                events.append(event)
            except Empty:
                break
        return events 
   
    def event_to_dict(self,event,path):
        event_dict = {}
        for k in event.__dict__:
            kk = 'event'+k if k != '_event_type' else 'event_type' 
            event_dict[kk] = getattr(event,k)
        event_dict['event_src_path_rel']=self.rel_path(path,event.src_path)
        if hasattr(event,'dest_path'):
            event_dict['event_dest_path_rel'] = self.rel_path(path,event.dest_path)
        return event_dict

    # return event file path relative to root
    def rel_path(self,base,path):
        return path.replace(base+sep,'')

