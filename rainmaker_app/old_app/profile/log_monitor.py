import glob
import os

from yaml import safe_load

from rainmaker_app.lib import Tail, logger, RegexDict, FsActions

class LogMonitor(object):
    def __init__(self,log_dir,pattern='*.log',ignore_events=[]):
        self.ignore_events = ignore_events
        self.log_dir = log_dir
        self.log = logger.create(self.__class__.__name__)
        self.fs = FsActions()        
        self.fs.mkdir(log_dir)
        self.pattern = pattern
        self.tails = {}
    
    def get_events(self):
        ''' Scan log files for new events '''
        self.scan_files()
        return self.scan_events()

    def scan_files(self):
        ''' Scan directory for incoming log files'''
        for p in glob.glob(os.path.join(self.log_dir,self.pattern)):
            if p in self.tails:
                continue
            f=open(p,'r')
            tail = Tail(f)
            log_filter=LogFilter(self.log,self.ignore_events)
            tail.filter = log_filter.filter
            self.tails[p]=tail

    def scan_events(self):
        ''' Scan log files for events '''
        events = []
        for p,t in self.tails.iteritems():
            # keep position in case file replaced
            t.reseek()
            for event in t.new_lines():
                events.append(event)
        return events 

class LogFilter(object):
    ''' Custom Tail filter for recieving fs events '''
    def __init__(self,log,ignore_events=[]):
        self.log = log
        self.timestamp = 0
        self.nice_paths = RegexDict()
        self.nice_paths.add_regex('nice','^[a-zA-Z0-9]+')
        self.ignores = RegexDict()
        for v in ignore_events:
            self.ignores.add_fnmatch(v,v)

    def filter(self,line):
        ''' A callback function used for filtering lines from Tail'''
        try:
            event = __line_to_event__(line)
            timestamp = int(event['timestamp'])
            # we dont need to look for dest path
            # because it should have been logged
            # as a seperate event
            path = event['event_src_path_rel'] 
            p =  self.ignores.search(path)
            nice = self.nice_paths.search(path)
            
            if p:
                self.log.info('Ignoring event due to pattern: %s' % p)
                return False

            # search for and remove malicious paths    
            if not nice or '..' in path:
                self.log.warn('Ignoring malicious path: %s' % path)
                return False
        except:
            self.log.warn( 'Malformed line in fs log' )
            self.log.debug(line)
            return False
        
        if timestamp < self.timestamp:
            self.log.info('Ignoring event due to timestamp: %s' % timestamp)
            return False
        
        self.timestamp = timestamp
        return event

def __line_to_event__(line):
    ''' only return keys for valid event '''
    result={}
    dat = safe_load(line)
    keys=[
    'timestamp',
    'event_src_path_rel',
    'event_is_directory',
    'event_type'
    ]
    for k in keys:
        result[k] = dat[k]
    return result
