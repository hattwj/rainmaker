import re
import fnmatch

# A dictionary of regexes, search to return matching keys
class RegexDict(object):
    
    def __init__(self):
        self.patterns={}
     
    def add_regex(self,k,p):
        self.patterns[k] = re.compile(p)
    
    def add_fnmatch(self,k,p):
        self.patterns[k] = fnmatch.translate(p) 

    def search(self,val):
        result=[]
        for k,p in self.patterns.iteritems():
            if p.search(val):
                result.append(k)
        return result

