import os
import hashlib

from rainmaker.db.main import Sync, SyncFile

def md5Checksum(path, chunk_size=8192):
    m = hashlib.md5()
    fh = open(path, 'rb')
    while True:
        data = fh.read(chunk_size)
        if not data:
            break
        m.update(data)
    fh.close()
    return m.hexdigest()


def quick_check(sync_file):
    ''' Check for file changes '''
    with open( sync_file.path, 'rb' ) as f:
        finfo = os.fstat(f.fileno()) 
    if sync_file.file_size != finfo.st_size:
        sync_file.file_size = finfo.st_size
        sync_file.file_hash = None
    if sync_file.mtime != finfo.st_mtime:
        sync_file.mtime = finfo.st_mtime
        sync_file.file_hash = None
    if sync_file.ctime != finfo.st_ctime:
        sync_file.ctime = finfo.st_ctime
        sync_file.file_hash = None
    if sync_file.inode != finfo.st_ino:
        sync_file.inode = finfo.st_ino
        sync_file.file_hash = None
    if sync_path.file_hash is None:
        sync_path.file_hash = md5Checksum(sync_file.path)
    sync_file.stime = utils.time_now()

def scan(session):
    def _scan(sync):
        # scan self
        for root, dirs, files in os.walk(sync.path):
            for f in dirs:
                fpath = os.path.abspath(os.path.join(root, f))
                _scan_dir(_find_or_init(sync, fpath))
            
            for f in files:
                fpath = os.path.abspath(os.path.join(root, f))
                _scan_file(_find_or_init(sync, fpath))
            
    def _scan_dir(sync_file):
        if sync_file.is_dir == False and sync_file.id is not None:
            sync_file.does_exist = False
            session.add(sync_file)
            sync_file = SyncFile(
                sync_id = sync_file.sync_id, 
                rel_path = sync_file.rel_path)
        sync_file.is_dir = True
        sync_file.does_exist = True
        session.add(sync_file)
    
    def _scan_file(sync_file):
        if sync_file.is_dir:
            sync_file.does_exist = False
            session.add(sync_file)
            sync_file = SyncFile(
                sync_id = sync_file.sync_id, 
                rel_path = sync_file.rel_path)
        sync_file.is_dir = False
        sync_file.does_exist = True
        print(sync_file.id, sync_file.sync_id)
        quick_check(sync_file)
        session.add(sync_file) 

    def _find_or_init(sync, fpath):
        rel_path = sync.rel_path(fpath)
        sync_file = session.query(SyncFile).\
            filter(SyncFile.sync_id == sync.id, 
                    SyncFile.rel_path == rel_path).first()
        if not sync_file:
            sync_file = SyncFile(sync_id=sync.id, rel_path=rel_path)
        sync_file.sync = sync
        sync_file.path = fpath
        return sync_file

    def _check_for_deleted(sync):
        '''
            Mark all files that didn't show up in scan as deleted
        '''
        statement = session.query(SyncFile).filter(SyncFile.does_exist==True,
            SyncFile.sync_id == sync.id,
            SyncFile.updated_at < sync.updated_at).\
                update({'does_exist': False})
    print(777888)        
    for sync in session.query(Sync).all():
        print(88888)
        _scan(sync)
        _check_for_deleted(sync)
        session.commit()

class RollingHash(object):
    def __init__(self, hexdigest=None):
        self._hexdigest = hexdigest

    def update(self, msg):
        m = hashlib.md5()
        m.update('%s%s' % (str(self._hexdigest), msg) )
        self._hexdigest = m.hexdigest()

    def hexdigest(self):
        return self._hexdigest

