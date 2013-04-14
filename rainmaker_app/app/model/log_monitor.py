import glob


from .tail import Tail

class LogMonitor(object):
    def __init__(self,log_dir,pattern='*.log'):
        self.log_dir = log_dir
        self.pattern = pattern
        self.tails = {}

    def scan_files(self):
        ''' Scan directory for incoming log files'''
        for p in glob.glob(log_dir(self.pattern)):
            if p in self.tails:
                continue
            f=open(p,'r')
            self.tails[p]=Tail(f)
            self.tails[p].filter_num = 0

    def scan_events(self):
        ''' Scan log files for events '''
        events = []
        for p,t in self.tails.iteritems():
            # keep position in case file replaced
            t.reseek()
            for line in t.new_lines():
                events += self.__line_to_event__(line)
        return events

    def __line_to_event__(self,line):
        dat = safe_load(line)
        return dat
                
        
def log_filter(self,line):
    ''' A callback function used for filtering lines from Tail'''
    dat=line.split(' ')
    try:
        n = int(dat[0])
    except TypeError:
        self.log.warn( 'malformed line in fs log' )
        self.log.debug(line)

    if n < self.filter_num:
        return False
    self.filter_num = n
    return line

