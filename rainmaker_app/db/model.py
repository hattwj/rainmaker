import os

from threading import Lock

from twisted.enterprise import adbapi
from twisted.internet import defer

from twistar.dbobject import DBObject
from twistar.registry import Registry

#from db_migrate import initDB
#from mysql_config import initDB, tearDownDB
#from postgres_config import initDB, tearDownDB
from time import time
class SyncPath(DBObject):
    ''' Model status of file system between scans '''

    HASMANY = ['my_files']

    scanned_at      = 0
    scan_started_at = 0
    
    _count_scanned  = 0
    _count_stale    = 0
    _count_no_change = 0
    _count_new      = 0
    _count_deleted  = 0
    _lock_scanned   = Lock()
    _lock_stale     = Lock()
    _lock_no_change = Lock()
    _lock_deleted   = Lock()
    _lock_new       = Lock()
    
    def _reset_counters(self):
        self._count_scanned = 0
        self._count_stale = 0
        self._count_new = 0
        self._count_deleted = 0
        self._count_no_change = 0
    
    def _inc_new(self):
        self._lock_new.acquire()
        self._count_new += 1
        self._lock_new.release()
    
    def _inc_deleted(self, amount=1):
        self._lock_deleted.acquire()
        self._count_deleted += amount
        self._lock_deleted.release()

    def _inc_stale(self):
        self._lock_stale.acquire()
        self._count_stale += 1
        self._lock_stale.release()

    def _inc_no_change(self):
        self._lock_no_change.acquire()
        self._count_no_change += 1
        self._lock_no_change.release()

    def _scan_stats(self):
        return {
            'scanned_at': self.scanned_at,
            'count_scanned': self._count_scanned,
            'count_new': self._count_new,
            'count_stale': self._count_stale,
            'count_no_change': self._count_no_change,
            'count_deleted': self._count_deleted
        }

    def scan(self):

        @defer.inlineCallbacks
        def _scan(self, count=0):
            
            path = self.root

            self._lock_scanned.acquire()
            self._reset_counters()
            self.scan_started_at = int( round( time() * 1000 ) )  
            
            # scan self
            for root, dirs, files in os.walk(path):
                for f in files+dirs:
                    self._count_scanned += 1
                    yield self.update_my_file( os.path.join(root, f), count )  
            if self._count_scanned == 0:
                yield None
            
            # dont count dissapearing files
            self._count_scanned -= self._count_deleted
            yield self.find_deleted_my_files()
            defer.returnValue(self)
        
        def _scan_done(self):
            self.scanned_at = self.scan_started_at
            result = self._scan_stats()
            self._lock_scanned.release()
            self.save()
            return result
        
        d = _scan(self)
        d.addCallback(_scan_done)
        return d

    @defer.inlineCallbacks
    def update_my_file( self, path, count):
        my_file = yield MyFile.findOrCreate( 
            path=path, 
            sync_path_id=self.id
        )
        
        my_file.scan()

        if my_file.is_stale():
            self._inc_stale()
        elif my_file.is_no_change():
            self._inc_no_change()
        elif my_file.is_new():
            self._inc_new()
        elif my_file.is_deleted():
            # race condition between os.walk and scan?
            self._inc_deleted()
        else:
            print 'Debug in scanner'
            print my_file
        yield my_file.save()

    @defer.inlineCallbacks
    def find_deleted_my_files(self):
        ''' Find files that need to be marked as deleted '''
        missed = yield MyFile.find( where=[
            '''sync_path_id = ? AND scanned_at < ? AND state != ?''',
            self.id,
            self.scan_started_at,
            MyFile.DELETED])
        
        for f in missed:
            f.scan()
            if f.is_deleted():
                f.save()
                self._inc_deleted()
            else:
                print 'Debug me'
        defer.returnValue(self)


from rainmaker_app.lib.lib_hash import md5Checksum as checksum
class MyFile(DBObject):

    BELONGSTO = ['sync_path']
    HASMANY = ['file_versions']

    #State Constants
    ERROR      = 999
    CONFLICT   = 888
    DELETED    = 4
    MODIFIED   = 3
    MOVED      = 2
    NO_CHANGE  = 1
    NEW = 0
    
    CREATE_NEW_AND_SAVE = [MODIFIED, MOVED]

    #Defaults
    state = NEW
    path = None
    inode = None
    fhash = None
    my_file_id = None
    is_dir = None

    #Column names
    columns = ['id', 'fhash', 'inode', 'mtime', 'ctime', 'sync_path_id', 'path' ]
    fstat_columns = ['inode', 'mtime', 'ctime' ]
    
    #Original values
    data_was = {}
    
    @classmethod
    def find_many(klass, arr, col='id'):
        where_ids = []
        where = ''
        for val in arr:
            where_ids.append( val )
            if where == '':
                where = "%s = ?" % col
            else:
                where += ' OR %s = ?' % col
        where_ids.insert(0, where)
        return klass.find(where=where_ids)


    def __init__(self, **kwargs):
        DBObject.__init__(self, **kwargs)
        ''' Save original values ''' 
        self.data_was = self.toHash( self.columns )

    def afterInit(self):
        if self.state == self.NEW:
            if self.fhash != None or self.is_dir == True:
                self.state = self.NO_CHANGE
    
    def has_fstat_changed(self):
        ''' Check for file changes '''
        f=open( self.path, 'rb' )
        finfo = os.fstat(f.fileno()) 
        f.close()
        self.size = finfo.st_size
        self.inode = finfo.st_ino
        self.mtime = finfo.st_mtime
        self.ctime = finfo.st_ctime

        for k in self.fstat_columns:
            if getattr(self,k) != self.data_was[k]:
                return True
        return False

    def beforeCreate(self):
        ''' '''
        self.created_at = int( round( time() * 1000 ) )
 
    def beforeSave(self):
        if self.state == self.MODIFIED:
            self.state = self.NO_CHANGE
        self.updated_at = int( round( time() * 1000 ) )
        # change stored values
        self.data_was = self.toHash( self.columns )
        print self.data_was

    def is_new(self):
        ''' check if record is new '''
        return self.state == self.NEW
    
    def is_error(self):
        ''' check if record is new '''
        return self.state == self.ERROR

    def is_no_change(self):
        ''' check if record is new '''
        return self.state == self.NO_CHANGE
        
    def is_stale(self):
        ''' check if record is stale '''
        if self.state in self.CREATE_NEW_AND_SAVE:
            return True
        return False
 
    def is_deleted(self):
        return self.state == self.DELETED

    def reset(self):
        '''
        Reset values
        '''
        if self.id == None:
            return False
        print self.data_was
        for k, v in self.data_was.iteritems():
            setattr(self,k,v)
        return True

    def scan(self):
        '''
        create or update file info of path
        check for changes
        '''
        
        def _scan(self):
            if self.state == self.DELETED:
                self.state = self.MODIFIED

            if  os.path.isdir( self.path ):
                self.is_dir = True
                return 
            
            has_changed = self.has_fstat_changed()
                    
            if self.is_new() or has_changed:
                self.fhash = checksum( self.path )
            
            if has_changed and self.is_new() == False:
                self.state = self.MODIFIED
        
        self.scanned_at = int( round( time() * 1000 ) )
        try:
            _scan(self)
        except:
            if not os.path.exists( self.path ):
                self.state = self.DELETED
            else:
                self,state = self.ERROR

class FileVersion(DBObject):
    
    #State Constants
    ERROR      = 999
    CONFLICT   = 888
    DELETED    = 4
    MODIFIED   = 3
    MOVED      = 2
    NO_CHANGE  = 1
    NEW        = 0

    #Defaults
    sync_path_id = NEW
    state        = NEW
    inode        = NEW
    fhash        = None
    my_file_id   = NEW
    
    #Column names
    columns = ['id', 'fhash', 'inode', 'my_file_id', 'parent_id', 'sync_path_id', 'version' ]

class Difference(DBObject):
    HAS_MANY = ['file_versions']

    @classmethod
    def compare(klass, id1, id2):
        return  klass.find( where=["sync_path_id = ? or sync_path_id = ?", id1, id2]) 
   
    @classmethod
    @defer.inlineCallbacks
    def resolve(klass, id1, id2):
        """ resolve differences between two sync_paths """
        # find differences
        diffs = yield klass.compare(id1, id2)
        where_ids = []
        for myfile in diffs:
            where_ids.append( myfile.id )
        diffs = yield MyFile.find_many(where_ids)

        result = []
        while 0 < len( diffs ):

            r = FileResolver( diffs.pop() )
            r.resolve( diffs )
            result.append( r )
        defer.returnValue( result )

class FileResolver(object):
    """ resolve differences between multiple files """
    state = None
    my_file = None
    vs_file = None

    related = None
    related_idx = None
    conflict = None

    def __init__(self, my_file):
        self.my_file = my_file
        self.vs_file = None
        self.conflict = None
        self.related = []
        self.related_idx = []

    def resolve(self, arr):
        """ """
        self.arr = arr
        
        if self.my_file.is_dir == False and self.__modified_file():
            self.state = 'modified'
        elif self.my_file.is_dir == False and self.__moved_file(arr):
            self.state = 'moved'
        elif self.__deleted():
            self.state = 'deleted'
        else:
            self.state = 'new'
        
        if self.state != 'new':
            self.related = pop_multiple( self.related_idx )
            self.conflict =  self._conflict_check()
    
    def _conflict_check(self):
        
        for ver in self.related.file_versions:
            pass


    def __moved_file(self):
        # check for moved file
        rules = [
            [ 'path',   '!=', self.my_file.path],
            [ 'fhash',  '=',  self.fhash]
        ]
        idx = nested_index(arr, rules )
        if len( idx ) == 1:
            self.related_idx = arr
            return True
        return False

    def __modified_file(self):
        # check for modified file
        rules = [
            [ 'path', '=', self.my_file.path],
            [ 'fhash', '!=', self.fhash]
        ]
        idx = nested_index(arr, rules )
        if len( idx ) == 1:
            self.related_idx = arr
            return True

    def __deleted(self):
        # check for deleted file
        rules = [
            [ 'path', '=', self.my_file.path],
            [ 'state', '=', MyFile.DELETED]
        ]
        idx = nested_index(arr, rules )
        if len( idx ) == 1:
            self.related_idx = arr
            return True

def pop_multiple(arr, idx, pop=True):
    """ pop multiple indecies from array """
    result = []
    for i in sorted(idx, reverse=True):
        if pop:
            result.append( arr.pop(i) )
        else:
            result.append( arr[i] )

    return result

def nested_index(self,arr, rules):
    """ search array and pop matching values """
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

class SchemaMigration(DBObject):
    pass

Registry.register(MyFile, SyncPath, FileVersion, SchemaMigration)
Registry.register(Difference)
