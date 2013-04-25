import glob
import os

from yaml import safe_load

from rainmaker_app.lib import Tail, logger

class LogMonitor(object):
    def __init__(self,log_dir,pattern='*.log'):
        self.log_dir = log_dir
        self.log = logger.create(self.__class__.__name__)
        try:
            os.mkdir( log_dir)
            os.path.isdir( log_dir )
        except OSError,e:
            pass            
        self.pattern = pattern
        self.tails = {}
    
    def get_events(self):
        self.scan_files()
        return self.scan_events()

    def scan_files(self):
        ''' Scan directory for incoming log files'''
        for p in glob.glob(os.path.join(self.log_dir,self.pattern)):
            if p in self.tails:
                continue
            f=open(p,'r')
            tail = Tail(f)
            log_filter=LogFilter(self.log)
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
    def __init__(self,log):
        self.log = log
        self.timestamp = 0

    def filter(self,line):
        ''' A callback function used for filtering lines from Tail'''
        try:
            event = __line_to_event__(line)
            timestamp = int(event['timestamp'])
        except:
            self.log.warn( 'malformed line in fs log' )
            self.log.debug(line)
            return False
        
        if timestamp < self.timestamp:
            return False
        
        self.timestamp = timestamp
        return event

def __line_to_event__(line):
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


