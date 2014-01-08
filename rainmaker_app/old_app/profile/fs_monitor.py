# give timestamps to events
from calendar import timegm
from time import gmtime

from os import sep

# Queue imports for different python versions
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from yaml import safe_dump

from watchdog.events import PatternMatchingEventHandler
from watchdog.events import FileSystemMovedEvent
from watchdog.events import FileSystemEvent


from rainmaker_app.lib import logger#, Callbacks
class FsMonitor(PatternMatchingEventHandler):
    event_log_style= '%(message)s'

    def __init__(self,watch_path,log_path,ignore_patterns=None):
        PatternMatchingEventHandler.__init__(self,ignore_patterns=ignore_patterns)
        self.event_q = Queue()
        log_name = log_path
        self.fs_log = logger.log_to_file(log_path,log_path,style=self.event_log_style,level='debug')
        self.log = logger.create(self.__class__.__name__)
        self.watch_path = watch_path

    ## store events in queue
    def on_any_event(self,event_obj):
        event = self.__event_to_dict__(event_obj,self.watch_path)
        event['timestamp'] = '%s' % timegm(gmtime())
        self.log.info('FS Event')
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
    def get_events(self):
        events = []
        while True:
            try:
                event = self.event_q.get_nowait() 
                events.append(event)
                self.fs_log.debug(safe_dump(event).replace("\n",''))

            except Empty:
                break
        #self.callbacks.trigger('get_events',events=events)
        return events 
   
    def __event_to_dict__(self,event,path):
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
