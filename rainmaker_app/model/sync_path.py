import hashlib
from threading import Lock
from os import urandom
from os.path import abspath

from . common import *
from . my_file import MyFile

from rainmaker_app.lib.lib_hash import RollingHash
from rainmaker_app.lib.util import time_now
from rainmaker_app.lib.net.cert import hashify

HROUNDS=12

class SyncPath(Base):
    ''' Model status of file system between scans '''

    HASMANY = ['my_files']
    BEFORE_VALIDATE = ['resolve_root']
    BEFORE_CREATE = ['_gen_pass', '_gen_guid']
    BEFORE_SAVE = ['scan']
    ATTR_ACCESSIBLE = [
        'machine_name',
        'rolling_hash',
        'state_hash'
    ]

    scanning        = False
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

    @classmethod
    @defer.inlineCallbacks
    def new(klass, **kwargs):
        sync = yield klass.findOrCreate(**kwargs)
        result = yield sync.save()
        defer.returnValue(sync)
    def _gen_pass(self):
        if not self.password_rw:
            self.password_rw = urandom(80).encode('base-64')
    def _gen_guid(self):
        if not self.guid:
            h = hashlib.md5()
            h.update(self.password_rw[:9])
            self.guid = h.hexdigest()
    @property
    def _password(self):
        return self.password_rw[9:]
    @defer.inlineCallbacks
    def is_state_hash_stale(self):
        ''' check files for change '''
        my_files = yield MyFile(where=[
            '''
            sync_path_id = ? AND 
            updated_at > ? AND
            next_id IS NULL AND
            state != ?
            ''',
            self.id,
            self.state_hash_updated_at,
            MyFile.DELETED
        ])
        if my_files:
            defer.returnValue( True )
        defer.returnValue( False )

    @property
    def machine_name(self):
        from rainmaker_app import app
        return app.machine_name

    @defer.inlineCallbacks
    def refresh_state_hash(self, incremental = False):
        '''
            recalculate state
        '''        
        if incremental:
            my_files = yield MyFile.active_files_since(self.id, self.state_hash_updated_at)
        else:
            my_files = yield MyFile.active_files(self.id)
            self.state_hash = None

        f_ubound = len(my_files) - 1
        h = RollingHash()
        bufr = ''
        h.update(bufr)
        for i, f in enumerate(my_files):
            bufr += '%s-%s-%s-%s' % (f.path, f.state, f.fhash, f.is_dir)
            if len(bufr) > 4096 or i == f_ubound:
                h.update(bufr)
                bufr = ''
        self.state_hash = str(h.hexdigest())    
        self.rolling_hash = str(h.hexdigest())    
        self.state_hash_updated_at = self.time_now() 
        defer.returnValue( self.state_hash )
    
    def resolve_root(self):
        self.root = abspath(self.root)

    ##
    # State counters
    def _reset_counters(self):
        ''' mutexed counters '''
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
        '''
            scan files/subdirs
        '''
        log.msg('scanning: %s' % self.root)
        @defer.inlineCallbacks
        def _scan(self, count=0):
            ''' start scan '''
            path = self.root

            self._lock_scanned.acquire()
            self._reset_counters()
            self.scan_started_at = time_now()  
            
            # scan self
            for root, dirs, files in os.walk(path):
                for f in files+dirs:
                    self._count_scanned += 1
                    yield self.update_my_file( os.path.join(root, f), count )  
            if self._count_scanned == 0:
                yield None
            
            # don't count disappearing files
            self._count_scanned -= self._count_deleted
            yield self.find_deleted_my_files()
            yield self.refresh_state_hash()
            defer.returnValue(self)
        
        def _scan_done(self):
            ''' callback for when callback complete '''
            log.msg('scan complete')
            self.scanned_at = self.scan_started_at
            result = self._scan_stats()
            self._lock_scanned.release()
            return result
        
        d = _scan(self)
        d.addCallback(_scan_done)
        return d

    @defer.inlineCallbacks
    def update_my_file( self, path, count):
        my_file = yield MyFile.findOrCreate( 
            path=path, 
            sync_path_id=self.id,
            cached_associations={'_sync_path': self}
        )
        my_file.scan()

        if my_file.is_stale():
            self._inc_stale()
        elif my_file.is_no_change():
            self._inc_no_change()
        elif my_file.is_new():
            log.msg('new file: %s' % path)
            self._inc_new()
        elif my_file.is_deleted():
            # race condition between os.walk and scan?
            self._inc_deleted()
        else:
            msg = 'Scanned File: %s has unknown state' % my_file.path
            raise ScannerError(msg)
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
                print 'A file that we thought was deleted still exists'
        defer.returnValue(self)

class ScannerError(Exception):
    ''' Error while scanning files '''
    pass

def beforeValidate(sync_path):
    return sync_path.beforeValidate()

def password_rw_len_validator(sync_path):
    if len(sync_path.password_rw) < 40:
        sync_path.errors.add('password_rw', 'too short')
        return False
    if len(sync_path.password_rw) > 4000:
        sync_path.errors.add('password_rw', 'too long')
        return False
    return True

SyncPath.addValidator(beforeValidate)
SyncPath.addValidator(password_rw_len_validator)
# TODO: add sql unique also
SyncPath.validatesUniquenessOf('root')

