from rainmaker_app.model.common import *

class FileResolver(object):
    """ resolve differences between multiple files """
    
    #State Constants
    CONFLICT        = 5
    DELETED         = 4
    MODIFIED        = 3
    MOVED           = 2
    NO_CHANGE       = 1
    NEW             = 0
    
    def __init__(self, my_file=None, *peers):
        """ init resolver consisting of at least one file """
        if not peers:
            peers = []
        self._init_properties(my_file)  # Init class properties
        self._init_peers(peers)         # Check if init as peer

    def _init_peers(self, peers):
        """ init peers and assert peer equality """
        self.peer_files = list(peers)
        if self.my_file:
            self.peer_files.append( self.my_file )
        # check if assert required
        if len(peers) > 0:
            return
        # verify peer files
        rules = _full_match_rules( self.my_file )
        peer_ids = _pattern_index(peers[1:], rules, version=False)
        assert len(peer_ids) == len(peers) 

    @classmethod
    def _init_as_parent_of(klass, child):
        """ initialize class as parent of child if child present """ 
        resolver = klass( *child.parent_files )
        resolver.child = child
        return resolver

    @classmethod
    def _init_as_child_of(klass, parent):
        """ initialize class as child of parent if parent present """
        resolver = klass( *parent.child_files )
        resolver.parent = parent
        return resolver

    def _copy_relative(self, relative):
        """ copy attributes of relative when initialized as parent/child """
        self.related_files = relative.related_files
        self.conflict_files = relative.conflict_files
        self.unrelated_files = relative.unrelated_files
    
    def _update_parent(self):
        """ propagate remaining files upward"""
        if self._parent:
            self._parent._copy_relative(self)
            self._parent._update_parent()
    
    def _update_child(self):
        """ propagate remaining files downward"""
        if self._child:
            self._child._copy_relative(self)
            self._child._update_child()

    def _init_properties(self, my_file):
        """ init class variables """
        self._state = None
        self.my_file = my_file
        self._child = None
        self._last_child = None
        self._parent = None
        self._first_parent = None
        self.unrelated_files = []
        self.conflict_files = []
        self.related_files = []
        self.parent_files = []
        self.child_files = []
        self.peer_files = []

    def resolve_against(self, my_files):
        """ 
            Compare this my_file object with the files in arr
            - find which one should take precedence
            - find what type of change occurred
            - find out if this is a conflicting change
        """
        if not my_files:
            return

        # get array id of all being compared
        all_ids = [i for i, obj in enumerate(my_files)]

        # look for identical / peer files
        rules = _full_match_rules( self.my_file )
        peer_ids = _pattern_index(my_files, rules, version=False)

        # look to see if we match an old version
        child_ids = _pattern_index(my_files, rules, version=True)

        # look for files matching our last version
        parent_ids = []
        if self.my_file.versions:
            rules = _full_match_rules( self.my_file.versions[0] )
            parent_ids = _pattern_index(my_files, rules, version=False)

        # look for conflicts with current version
        conflict_ids = [i for i, m in enumerate(my_files) if _conflict_match(m, self.my_file)]
         
        # remove files matching our last version
        conflict_ids = list(set(conflict_ids) - set(parent_ids))

        # remove files that we match the last version of
        conflict_ids = list(set(conflict_ids) - set(child_ids))
        
        # get un/related ids
        related_ids = list(set(conflict_ids + child_ids + parent_ids))
        unrelated_ids = list(set(all_ids) - set(related_ids))

        # collect objects
        self.peer_files += [my_files[i] for i in peer_ids]
        self.parent_files = [my_files[i] for i in parent_ids]
        self.child_files = [my_files[i] for i in child_ids]
        self.related_files = [my_files[i] for i in related_ids] + self.peer_files
        self.unrelated_files = [my_files[i] for i in unrelated_ids]
        self.conflict_files = [my_files[i] for i in conflict_ids]
        
        # check for other matches in parents and children
        self._first_parent = self.first_parent
        self._last_child = self.last_child

    def result(self):
        """ peek at contents of resolve function"""
        return {
            'parents' : self.parent_files, 
            'children' : self.child_files,
            'related' : self.related_files,
            'peer' : self.peer_files,
            'unrelated' : self.unrelated_files,
            'conflict' : self.conflict_files
        }

    def remaining_files(self):
        """ return all files that are not parent/child """
        return self.conflict_files + self.unrelated_files

    @property
    def state(self):
        """ get final state of all related files """        
        if not self.peer_files:
            return None
        if self.conflict_files:
            return self.CONFLICT
        if self.last_child.my_file.state == self.my_file.DELETED:
            return self.DELETED
        child = self.last_child
        while child.parent:
            if child.parent.my_file.fhash != child.my_file.fhash:
                return self.MODIFIED
            if child.parent.my_file.is_dir != child.my_file.is_dir:
                return self.MOVED
            if child.parent.my_file.path != child.my_file.path:
                return self.MOVED
        return self.NEW         

    @property
    def child(self):
        """ init child or return none """
        if self._child == None and self.child_files:
            child = FileResolver._init_as_child_of(self)
            child.resolve_against( self.remaining_files() )
            self.child = child
        return self._child

    @child.setter
    def child(self, val):
        self._child = val
        self.child_files = self._child.peer_files
        self._copy_relative( self._child )
        self._update_parent()

    @property
    def parent(self):
        """ init parent or return none """
        if self._parent == None and self.parent_files:
            parent = FileResolver._init_as_parent_of(self)
            parent.resolve_against( self.remaining_files() )
            self.parent = parent
        return self._parent

    @parent.setter
    def parent(self, val):
        """ set parent """
        self._parent = val
        self.parent_files = self._parent.peer_files
        self._copy_relative( self._parent )
        self._update_child()

    @property
    def first_parent(self):
        """ get first parent of series """
        if self.parent:
            return self.parent.first_parent
        return self

    @property
    def last_child(self):
        """ get last child of series """
        if self.child:
            return self.child.last_child
        return self

def pop_multiple(arr, idx, pop=True):
    """ pop multiple indices from array """
    result = []
    for i in sorted(idx, reverse=True):
        if pop:
            result.append( arr.pop(i) )
        else:
            result.append( arr[i] )
    return result

def obj_matches_rules(obj, rules):
    """ see if object matches conditions """
    idx = []
    match = True
    for j, rule in enumerate(rules):
        key, op, val = rule
        obj_val = getattr(obj, key)
        if op == '=' and obj_val != val:
            match = False
            break
        if op == '!=' and obj_val == val:
            match = False
            break
    return match

def _full_match_rules( my_file ):
    """ generate rules for full match of my_file object """
    return [
        [ 'path', '=', my_file.path],
        [ 'sync_path_id', '!=', my_file.sync_path_id],
        [ 'fhash', '=', my_file.fhash],
        [ 'state', '=', my_file.state],
        [ 'size', '=', my_file.size],
        [ 'is_dir', '=', my_file.is_dir]
    ]

def _conflict_match( m1, m2 ):
    """ check for conflicts between two my_file objects """
    if _conflict(m1, m2):
        return True
    if m1.path == m2.path:
        return False
    if m1.versions and m2.versions:
        for m1v in m1.versions:
            if _pattern_index( m2.versions, _full_match_rules(m1v), False):
                return True
    return False

def _conflict(m1, m2):
    """ compare two files to see if they conflict """
    return m2.path == m1.path and (
    m2.fhash != m1.fhash or
    m2.state != m1.state or
    m2.size != m1.size or
    m2.is_dir != m1.is_dir )
    
def _pattern_index( my_files, rules, version=False ):
    """ return index of files matching rule """
    result = []
    for i, my_file in enumerate(my_files):
        match = False
        if version and my_file.versions:
            match = _pattern_index( my_file.versions, rules, False)
        elif not version:
            match = obj_matches_rules( my_file, rules)
        if match:
            result.append(i)
    return result
