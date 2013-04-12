import glob


from .tail import Tail

class EventLogParser(object):
    def __init__(self,log_dir,pattern):
        self.log_dir = log_dir
        self.pattern = pattern

    def scan_files(self):
        for p in glob.glob(log_dir(self.pattern)):
            if p in self.tails:
                continue
            f=open(p,'r')
            self.tails[p]=Tail(f)

    def scan_events(self):
        for p,t in self.tails.iteritems()
            for line in t.new_lines():
                print line
                
        


