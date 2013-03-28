import re

# A dictionary of regexes, search to return matching keys
class RegexDict(object):
    
    def __init__(self,data=None):
        self.data=data if data else []
        self.patterns={}
    
    def compile(self):
        if self.patterns:
            return False
        for k,v in self.data.iteritems():
            self.patterns[k]= re.compile(v)
        return True
    
    def add_regex(self,k,p):
        self.data[k]=p
        self.patterns={}

    def search(self,val):
        self.compile()
        result=[]
        for k,p in self.patterns.iteritems():
            if p.search(val):
                result.append(k)
        return result

