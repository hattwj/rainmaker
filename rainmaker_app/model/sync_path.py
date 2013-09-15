from threading import Lock

from . common import *
from . my_file import MyFile

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

