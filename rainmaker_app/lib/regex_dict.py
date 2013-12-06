import re
import fnmatch

class RegexDict(object):
    ''' A dictionary of regexes, search to return matching keys'''

    def __init__(self, regex_patterns=None, fnmatch_patterns=None, return_as=None):
        self.patterns={}
        self.values = {}
        self.return_types = ['key','both','match']
        if not return_as:
            self.return_as = 'key'
        else:
            self.return_as = return_as

        if fnmatch_patterns:
            for k, p in fnmatch_patterns.iteritems():
                self.add_fnmatch(k,p)

        if regex_patterns:
            for k, p in regex_patterns.iteritems():
                self.add_regex(k,p)
     
    def add_regex(self,k,p):
        self.patterns[k] = re.compile(p)
        self.values[k] = p

    def add_fnmatch(self,k,p):
        self.values[k] = fnmatch.translate(p)
        self.patterns[k] = re.compile(self.values[k])

    def search(self,val, limit=0):
        return self._find( val, limit, False)
    
    def match(self,val, limit=0):
        return self._find( val, limit, True)

    def _find(self,val, limit, use_match):
        result=[]
        for k,p in self.patterns.iteritems():
            if use_match:
                m = p.match(val)
            else:
                m = p.search(val)
            if m:
                result.append(self._found_add(k,m))
                if limit and limit >= len(result):
                    break
        if limit == 1 and result:
            result = result[0]
        return result

    def _found_add(self, key, match):
        if self.return_as == 'key':
            return key
        if self.return_as == 'match':
            return match
        return [key, match]
        
