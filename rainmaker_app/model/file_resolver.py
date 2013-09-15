from . common import *

class FileResolver(object):
    """ resolve differences between multiple files """
    def __init__(self, my_file):
        # Init class properties
        self.my_file = my_file
        self.state = None
        self.vs_file = None
        self.conflict = None
        self.related = [my_file]
        self.related_idx = []

    def resolve(self, my_files):
        """ 
            Compare this my_file object with the files in arr
            - find which one should take precedence
            - find what type of change occurred
            - find out if this is a conflicting change
        """
        
        if my_file.is_dir == False and self.__modified_file(my_file):
            self.state = 'modified'
        elif my_file.is_dir == False and self.__moved_file(my_file):
            self.state = 'moved'
        elif self.__deleted():
            self.state = 'deleted'
        else:
            self.state = 'new'
        if self.state != 'new':
            self.related = pop_multiple( self.related_idx )
            self.conflict =  self._conflict_check()
    
    def conflicts_check(self):
        """ Check my_file and vs_file to see if they are conflicting """
        rules = [
            [ 'path', '=', self.my_file.path],
            [ 'sync_path_id', '!=', self.my_file.sync_path_id],
            [ 'fhash', '=', self.my_file.fhash],
            [ 'size', '=', self.my_file.size],
            [ 'is_dir', '=', self.my_file.is_dir],
        ]
        no_conflict_ids = self._pattern_index(self.my_files, rules)
        

    def _moved_file(self):
        """ check for moved file """
        rules = [
            [ 'path',   '!=', self.my_file.path],
            [ 'fhash',  '=',  self.fhash]
        ]
        idx = nested_index(arr, rules )
        if len( idx ) == 1:
            self.related_idx = arr
            return True
        return False

    def _pattern_index(self, my_files, rules):
        result = []
        for i, my_file in enumerate(my_files):
            idx1 = nested_index( [my_file], rules)      
            idx2 = nested_index( my_file.versions, rules)
            if (idx1 or idx2):
                result.append([i,idx2])
        return result
    
    def compare_with(self, my_files):
        self.my_files = my_files
    
    def related_ids(self):
        """
            Search for the files that:
            - shared a path name
        """
        related_ids = []
        rules = [[ 'path', '=', self.my_file.path]]
        self.ids = self._pattern_index(self.my_files, rules)
        return self.ids

def pop_multiple(arr, idx, pop=True):
    """ pop multiple indecies from array """
    result = []
    for i in sorted(idx, reverse=True):
        if pop:
            result.append( arr.pop(i) )
        else:
            result.append( arr[i] )
    return result

def nested_index(arr, rules):
    """ search array and return index of matching values """
    idx = []
    for i, item in enumerate(arr):
        match = True
        for j, rule in enumerate(rules):
            key, op, val = rule
            obj_val = getattr(item, key)
            if op == '=' and obj_val != val:
                match = False
                break
            if op == '!=' and obj_val == val:
                match = False
                break
        if match:
            idx.append( i )
    return idx


