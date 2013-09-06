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
        def _scan(self, path, count=0):
            self._lock_scanned.acquire()
            self._reset_counters()
            self.scan_started_at = int( round( time() * 1000 ) )  

            for root, dirs, files in os.walk(path):
                for f in files+dirs:
                    print 'an f: -> ' + f
                    self._count_scanned += 1
                    yield self.update_my_file( os.path.join(root, f), count )  
            if self._count_scanned == 0:
                yield None
            yield self.find_deleted_my_files()
            defer.returnValue(self)
        
        def _scan_done(self):
            print 'Scan Done'
            self.scanned_at = self.scan_started_at
            result = self._scan_stats()
            self._lock_scanned.release()
            print result
            self.save()
            return result
        
        d = _scan(self, self.root)
        #d.addCallback( self.find_deleted_my_files() )
        #self.find_deleted_my_files()
        d.addCallback(_scan_done)
        return d

    @defer.inlineCallbacks
    def update_my_file( self, path, count):
        my_file = yield MyFile.findOrCreate( 
            path=path, 
            sync_path_id=self.id
        )
        
        if my_file.is_new():
            self._inc_new()

        my_file.scan()

        if my_file.is_stale():
            self._inc_stale()
        elif my_file.is_no_change():
            self._inc_no_change()
        else:
            print my_file
        yield my_file.save()

    @defer.inlineCallbacks
    def find_deleted_my_files(self):
        print self
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
        defer.returnValue(self)

from rainmaker_app.lib.lib_hash import md5Checksum as checksum

class MyFile(DBObject):
    BELONGSTO = ['sync_path']
    
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
    inode = 0
    fhash = None
    my_file_id = 0

    #Column names
    columns = ['id', 'fhash', 'inode', 'mtime', 'ctime', 'sync_path_id' ]
    fstat_columns = ['inode', 'mtime', 'ctime' ]
    
    #Original values
    data_was = {}

    def afterInit(self):
        ''' Save original values '''
        
        if self.state == self.NEW:
            if self.fhash != None or self.is_dir == True:
                self.state = self.NO_CHANGE
    
    def has_fstat_changed(self):
        ''' Check for file changes '''
        self.data_was = self.toHash( self.columns )

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
        for k, v in self.data_was:
            set(self,k,v)
        return True

    def scan(self):
        '''
        create or update file info of path
        check for changes
        '''
        
        self.scanned_at = int( round( time() * 1000 ) )
        
        if not os.path.exists( self.path ):
            self.state = self.DELETED
            return

        if  os.path.isdir( self.path ):
            self.is_dir = True
            return 
        
        has_changed = self.has_fstat_changed()
                
        if self.is_new() or has_changed:
            self.fhash = checksum( self.path )
        
        if has_changed and self.is_new() == False:
            self.state = self.MODIFIED

        self.scanned_at = int( round( time() * 1000 ) )

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

class SchemaMigration(DBObject):
    pass


Registry.register(MyFile, SyncPath, FileVersion, SchemaMigration)
