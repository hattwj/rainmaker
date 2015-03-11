from rainmaker.db.views import sync_diff

# Decision constants
CONFLICT_MINE   = 7 # Decided to keep mine
CONFLICT_THEIRS = 6 # Decided to keep theirs

#State Constants
CONFLICT        = 5 # Undecided conflict
UPDATE_THEIRS   = 3
UPDATE_MINE     = 2
NO_CHANGE       = 1 # Nothing changed
NEW             = 0 # New file

def commit_resolve(state, 

def resolve_syncs(sync, host):
    """ compare sync paths and find conflicts/updates"""        
    s_files, h_files = sync_diff(sync.id, host.id)
    files = s_files + h_files
    resolvers = []
    while len(files) > 0:
        # resolve differences
        resolved_set = resolve_files(files)
        resolvers.append(resolved_set)
    return resolvers

def resolve_files(files):
    ''' Resolve first file in array '''
    # check self, vers, other/vers for cmp any
    target, related = find_cmp_targets(files)
    state = resolve_state(target, related)
    if state == NEW:
        # else look for full matches:
        target, related = find_full_targets(files)
        state = resolve_state(target, related)
    return (state, target, related)
            
def resolve_state(target, related):
    # on first find cmp
    if target.is_head and related.is_none:
        # target is new file
        return NEW
    elif target.is_head and related.is_head:
        # nothing changed
        return NO_CHANGE
    elif target.is_head and related.is_ver:
        # (1) head? vs (n) ver? we lead - mark thead cmp
        return UPDATE_THEIRS
    elif target.is_ver and related.is_ver:
        # ver vs ver = conflict -
        return CONFLICT
    elif target.is_ver and related.is_head:
        # (n) ver vs (1) head they lead -
        return UPDATE_MINE
    raise ResolutionError()

def find_cmp_targets(files):
    ''' peek on first element of array and find match
        - pop matches if found
    '''    
    t_state = ResolverQuery(files).first().require('cmp_id', 'cmp_ver')
    if t_state.target:
        r_state = ResolverState(files).find(cmp_id=t.cmp_id, 
                cmp_ver=t.cmp_ver)
    else:
        t_state = ResolverState(files).add_first()
        t = t_state.head
        r_state.find(cmp_id=t.id, cmp_ver=)
    return t_state, r_state

class ResolutionError(Exception):
    pass

class ResolverQuery(object):
    ''' Holds information about resolution state '''
    is_none = True
    is_ver = False
    is_head = False
    head = None
    ver = None
    target = None
    
    def __init__(self, files):
        self.files = files
        self._search_ = files

    def first(self):
        ''' Search only first '''
        self._search_ = [self.files[0]]
        return self
    
    def add_first(self):
        ''' Dont search, just select first '''
        self.add(self.files[0])
        return self

    def find(self, **kwargs):
        ''' Search Files and versions for first match '''
        for f in self._search_:
            if where_attrs_equal(f, kwargs):
                self.add(f)
                return self
            for v in f.vers:
                if where_attrs_equal(v, kwargs):
                    self.add(f, v)
                    return self
        return self    
         
    def require(self, *args):
        ''' Search Files and versions for first not null '''
        for f in self._search_:
            if require_not_null(f, args):
                self.add(f)
                return self
            for v in f.vers:
                if require_not_null(v, args):
                    self.add(f, v)
                    return self
        return self    

    def pop(self):
        ''' Remove found file from array '''
        self.files.remove(self.head) 

    def add(self, head, ver=None):
        ''' Add file and / or version '''
        self.is_none = False
        self.head = head
        if ver:
            self.is_ver = True
            self.ver = ver
            self.target = ver
        else:
            self.is_head = True
            self.target = head

def where_attrs_equal(f, attrs):
    ''' do keys and values match? '''
    for k, v in attrs.items():
        if getattr(f, k) != v:
            return False
    return True

def require_not_null(f, args):
    ''' Are all keys not null? '''
    for a in args:
        if getattr(f, a) is None:
            return False
    return True

class FileResolver(object):
    """ resolve differences between multiple files """
    
    #State Constants
    CONFLICT        = 5
    DELETED         = 4 
    MODIFIED        = 3 # File was altered
    MOVED           = 2 # File was moved (renamed)
    NO_CHANGE       = 1 # Nothing changed
    NEW             = 0 # New file

    def __repr__(self):
        return "<FileResolver state=%s, my_file_id=%s>" % (self.state, self.my_file.id)

    @classmethod
    def resolve_syncs(klass, sync, host):
        """ compare sync paths and find conflicts/updates"""        
        s_files, h_files = sync_diff(sync.id, host.id)
        files = s_files + h_files
        resolvers = []
        while len(files) > 0:
            # resolve differences
            a_file = files.pop()
            file_resolver = klass(a_file)
            file_resolver.resolve_against(files)
            resolvers.append(file_resolver)
            # prep for next round
            files = file_resolver.unrelated_files
        return resolvers

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
        peer_ids = _index_files(peers[1:], rules, version=False)
        assert len(peer_ids) == len(peers) 

    def _copy_relative(self, relative):
        """ copy attributes of relative when initialized as parent/child """
        for r in relative.related_files:
            if r not in self.related_files:
                self.related_files.append(r) 
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
        self.syncs = []

    def resolve_against(self, my_files):
        """ 
            Compare this my_file object with the files in arr
            - find which one should take precedence
            - find what type of change occurred
            - find out if this is a conflicting change
        """
        if not my_files:
            return
        
        print('MyFile', self.my_file)

        # look for identical / peer files
        rules = _full_match_rules(self.my_file)
        self.peer_files += _pop_files(my_files, rules, version=False)
        print('peer files')
        print(self.peer_files)

        # look to see if we match an old version
        self.child_files += _pop_files(my_files, rules, version=True)

        # look for files matching our last version
        if self.my_file.vers:
            rules = _full_match_rules( self.my_file.vers[0] )
            self.parent_files += _pop_files(my_files, rules, version=False)

        # look for conflicts with current version
        conflict_ids = [i for i, m in enumerate(my_files) if _conflict_match(m, self.my_file)]
        self.conflict_files = pop_multiple( my_files, conflict_ids)
        
        # get un/related ids
        self.related_files = self.peer_files + self.parent_files +\
            self.child_files + self.conflict_files
        self.unrelated_files = my_files

        # check for other matches in parents and children
        self._first_parent = self.first_parent
        self._last_child = self.last_child
        
    def result(self):
        """ peek at contents of resolve function"""
        return {
            'my_file': self.my_file,
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
        if self.last_child.my_file.does_exist == False:
            return self.DELETED
        child = self.last_child
        while child.parent:
            if child.parent.my_file.file_hash != child.my_file.file_hash:
                return self.MODIFIED
            if child.parent.my_file.is_dir != child.my_file.is_dir:
                return self.MOVED
            if child.parent.my_file.rel_path != child.my_file.rel_path:
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
        [ 'rel_path', '=', my_file.rel_path],
        [ 'file_hash', '=', my_file.file_hash],
        [ 'does_exist', '=', my_file.does_exist],
        [ 'file_size', '=', my_file.file_size],
        [ 'is_dir', '=', my_file.is_dir]
    ]

def _decision_match_rules(my_file):
    ''' '''
    return [
        ['cmp_id', '=', my_file.id],
        ['cmp_ver', '=', my_file.ver]
    ]

def _conflict_match( m1, m2 ):
    """ check for conflicts between two my_file objects """
    if _conflict(m1, m2):
        return True
    if m1.rel_path == m2.rel_path:
        return False
    if m1.vers and m2.vers:
        for m1v in m1.vers:
            if _index_files( m2.vers, _full_match_rules(m1v), False):
                return True
    return False

def _conflict(m1, m2):
    """ compare two files to see if they conflict """
    return m2.rel_path == m1.rel_path and (
    m2.file_hash != m1.file_hash or
    m2.does_exist != m1.does_exist or
    m2.file_size != m1.file_size or
    m2.is_dir != m1.is_dir )

def _pop_files(my_files, rules, version):
    ''' '''
    match_ids = _index_files(my_files, rules, version)
    return pop_multiple(my_files, match_ids)

def _index_files( my_files, rules, version=False ):
    """ return index of files matching rule """
    print('Index:', my_files, 'Rules', rules)
    result = []
    for i, my_file in enumerate(my_files):
        match = False
        if version and my_file.vers:
            match = _index_files( my_file.vers, rules, False)
        elif not version:
            match = obj_matches_rules( my_file, rules)
        if match:
            result.append(i)
    return result

class UnknownStateError(Exception):
    pass

