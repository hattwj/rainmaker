from collections import namedtuple
from rainmaker.db.views import sync_diff
from rainmaker.db.main import Download, Resolution

# Resolution State Constants
RES_ERROR       = Resolution.RES_ERROR      # Error during resolution
CONFLICT_MINE   = Resolution.CONFLICT_MINE   # Decided to keep mine
CONFLICT_THEIRS = Resolution.CONFLICT_THEIRS # Decided to keep theirs
CONFLICT        = Resolution.CONFLICT       # Undecided conflict
THEIRS_CHANGED  = Resolution.THEIRS_CHANGED # Change to host_file
MINE_CHANGED    = Resolution.MINE_CHANGED   # Change to sync_file
NEW             = Resolution.NEW # New file - Used in resolver_test:32

# File Status Constants
DELETED       = Resolution.DELETED      
MOVED         = Resolution.MOVED        
MODIFIED      = Resolution.MODIFIED     
CREATED       = Resolution.CREATED      
NO_CHANGE     = Resolution.NO_CHANGE


def get_downloads(db, resolutions):
    '''
        Store results from resolve syncs
        - Create Download record
        - update host_file to point at sync_file
    '''
    # Create download record
    def _add_download(r):
        dlo = db.query(Download).filter(
            Download.sync_id == r.host_file.host.sync.id,
            Download.rel_path == r.host_filr.rel_path
        ).first()
        if dlo is None:
            dlo = Download(sync_id = r.host_file.host.sync.id,
                rel_path=r.host_file.rel_path)
        dlo.from_host_file(r.host_file)
        db.add(dlo)

    for r in resolutions:
        # Add to download pool
        if r.state == THEIRS_CHANGED:
            _add_download(r)
    db.commit()
            
Resolution = namedtuple("Resolution", "status state sync_file host_file")

def get_resolutions(db, host):
    """ compare sync paths and find conflicts/updates"""
    sync_id, host_id = host.sync_id, host.id
    sync_files, host_files = sync_diff(db, sync_id, host_id)
    resolutions = []
    while len(sync_files) > 0 or len(host_files) > 0:
        # resolve differences
        resolution = resolve_files(sync_files, host_files)
        resolutions.append(resolution)
    return resolutions

def resolve_files(sync_files, host_files):
    ''' Resolve first file in array '''
    # check self, vers, other/vers for cmp any
    s_query, h_query = query_targets(sync_files, host_files)
    direction = resolution_direction(s_query, h_query)
    state = file_state(s_query.head, h_query.head) 
    return Resolution(status=direction, state=state, sync_file=s_query.head, host_file=h_query.head)

def file_state(sync_file, host_file):
    '''Check file state'''
    if host_file is None or sync_file is None:
        return CREATED
    if sync_file.does_exist != host_file.does_exist:
        return DELETED
    if sync_file.is_dir != host_file.is_dir:
        return DELETED
    if sync_file.rel_path != host_file.rel_path:
        return MOVED
    if sync_file.file_hash != host_file.file_hash:
        return MODIFIED
    return NO_CHANGE

def resolution_direction(target, related):
    '''Direction of change '''
    # on first find cmp
    if target.is_head and related.is_none:
        # target is new file
        return MINE_CHANGED
    if target.is_head and related.is_head:
        # both have same path and diff content
        return CONFLICT
    if target.is_head and related.is_ver:
        # (1) head? vs (n) ver?
        return THEIRS_CHANGED
    if target.is_ver and related.is_ver:
        # ver vs ver = conflict -
        return CONFLICT
    if target.is_ver and related.is_head:
        # my version has changed
        return MINE_CHANGED
    if target.is_none and related.is_head:
        # nothing changed
        return THEIRS_CHANGED
    '''
        Should not occur:
        none-ver, none-none, ver-none
    '''
    raise ResolutionStateError()

def query_targets(sync_files, host_files):
    ''' 
        Find files to compare 
    '''
    # check for first file that references another
    host_query = ResolverQuery(host_files).require('cmp_id', 'cmp_ver')
    sync_query = ResolverQuery(sync_files)
    host_file = host_query.target
    if host_file:
        # find referenced file
        sync_query.find(id=host_file.cmp_id, version=host_file.cmp_ver)
        if not sync_query.target:
            # referenced file not found, throw error
            raise ResolutionQueryError()
        return sync_query, host_query

    # get first file from array thats not empty
    lquery, rquery = (sync_query, host_query) if sync_files else (host_query, sync_query)
    lquery.add_first()
    query_file = lquery.head
    # see if any files match this by name
    rquery.without_versions().find(rel_path=query_file.rel_path)
    return sync_query, host_query

class ResolutionError(Exception):
    ''' Generic resolution error '''
    pass

class ResolutionQueryError(ResolutionError):
    '''Query expected result '''
    pass

class ResolverQuery(object):
    ''' Query interface for finding files that match a pattern '''
    
    is_none = True
    is_ver = False
    is_head = False

    head = None
    ver = None
    target = None
    _without_versions = False

    def __init__(self, files):
        self.files = files
        self._search_pool_ = files
    
    def without_versions(self):
        '''Dont search versions'''
        self._without_versions = True
        return self

    def first(self):
        ''' Search only first '''
        self._search_pool_ = [self.files[0]]
        return self
    
    def add_first(self):
        ''' Dont search, just select first '''
        self.add(self.files[0])
        return self

    def find(self, **kwargs):
        ''' Search Files and versions for first match '''    
        self.__search__(where_attrs_equal, kwargs)
        return self

    def require(self, *args):
        ''' Search Files and versions for first not null '''
        self.__search__(require_not_null, args)
        return self

    def __search__(self, filter_func, args):
        ''' Sesrch files for first match '''
        for f in self._search_pool_:
            if filter_func(f, args):
                self.add(f)
                return self
            if self._without_versions:
                continue
            for v in f.vers:
                if filter_func(v, args):
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
        self.pop()
        if ver:
            self.is_ver = True
            self.ver = ver
            self.target = ver
        else:
            self.is_head = True
            self.target = head

# Helper functions for ResolverQuery

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

