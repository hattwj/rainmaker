'''
TODO: 
    Add try except for file not found, mark deleted
    try scandir plugin for better walk performance
'''
import os

from rainmaker.file_system import hash_file
from rainmaker.db.main import Sync, SyncFile
from rainmaker import utils

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

chunk_size = 200000

def scan(session):
    ''' Scan all syncs in DB '''
    for sync in session.query(Sync).all():
        scan_sync(session, sync)

def scan_sync(session, sync):
    def _scan():
        # mark as scan started
        sync.stime_start = utils.time_now()
        session.add(sync)
        session.commit() 
        # scan sub dirs and files
        for root, dirs, files in os.walk(sync.path):
            # scan dirs
            for f in dirs:
                fpath = os.path.abspath(os.path.join(root, f))
                sync_file = _find_or_init(fpath)
                # skip if currently scanning
                if sync_file.stime_start < sync.stime_start:
                    scan_dir(session, sync_file)
            # scan files 
            for f in files:
                fpath = os.path.abspath(os.path.join(root, f))
                sync_file = _find_or_init(fpath)
                # skip if currently scanning
                if sync_file.stime_start < sync.stime_start:
                    scan_file(session, sync_file)
        # mark as scan complete
        sync.stime = utils.time_now()
        session.add(sync)
        session.commit()

    def _find_or_init(fpath):
        '''
            Check database or init new file
        '''
        rel_path = sync.rel_path(fpath) 
        sync_file = session.query(SyncFile).\
            filter(SyncFile.sync_id == sync.id, 
                    SyncFile.rel_path == rel_path).first()
        if not sync_file:
            sync_file = SyncFile(sync_id=sync.id, rel_path=rel_path)
            sync_file.stime = 0
            sync_file.stime_start = 0
        sync_file.sync = sync
        sync_file.path = fpath
        return sync_file

    def _check_for_deleted():
        '''
            Mark all files that didn't show up in scan as deleted
        '''
        session.query(SyncFile).filter(SyncFile.does_exist==True,
            SyncFile.sync_id == sync.id,
            SyncFile.stime_start < sync.stime_start).\
                update({'does_exist': False})
        session.commit()
        
    _scan()
    _check_for_deleted()


def refresh_sync(session, sync):
    '''
        Check database for new files to scan
    '''
    sync_files = session.query(SyncFile).filter(
        SyncFile.sync_id == sync.id,                
        SyncFile.does_exist == True,
        SyncFile.stime_start == 0).all()
    for sf in sync_files:
        if sf.is_dir:
            scan_dir(session, sf)
        else:
            scan_file(session, sf)

def scan_dir(session, sync_file):
    '''
        Scan and add this dir to db
    '''
    if sync_file.is_dir == False and sync_file.id is not None:
        # used to be a file, now its a dir
        sync_file.does_exist = False
        sync_file.stime_start = utils.time_now()
        sync_file.stime = utils.time_now()
        session.add(sync_file)
        sync_file = SyncFile(
            sync_id = sync_file.sync_id, 
            rel_path = sync_file.rel_path)
    sync_file.is_dir = True
    sync_file.does_exist = True
    sync_file.stime_start = utils.time_now()
    sync_file.stime = utils.time_now()
    session.add(sync_file)
    session.commit()

def scan_file(session, sync_file):
    ''' 
        Scan and add this file to db
            - slowest   md5
            - slow      adler32
            - fast      mtime, inode, ctime
    '''
    # Mark old directory as deleted if is_dir
    if sync_file.is_dir and sync_file.id is not None:
        sync_file.stime_start = utils.time_now()
        sync_file.stime = utils.time_now()
        sync_file.does_exist = False
        session.add(sync_file)
        session.commit()
    # start scan
    sync_file.stime_start = utils.time_now()
    sync_file.stime = 0
    sync_file.is_dir = False
    sync_file.does_exist = True
    # Check file state
    with open(sync_file.path, 'rb' ) as f:
        finfo = os.fstat(f.fileno())
    # Marking file_hash as None signals that a scan should be done 
    # file size changed?
    if sync_file.file_size != finfo.st_size:
        sync_file.file_size = finfo.st_size
        sync_file.file_hash = None
    # mtime changed?
    if sync_file.mtime != finfo.st_mtime:
        sync_file.mtime = finfo.st_mtime
        sync_file.file_hash = None
    # ctime changed?                        # maybe not needed?
    if sync_file.ctime != finfo.st_ctime:   #
        sync_file.ctime = finfo.st_ctime    #
        sync_file.file_hash = None          #
    # Inode changed?                        #
    if sync_file.inode != finfo.st_ino:     #
        sync_file.inode = finfo.st_ino      #
        sync_file.file_hash = None          #
    # Save progress
    session.add(sync_file)
    session.commit()
    # check if hashing needed 
    if sync_file.file_hash is None:
        # run hasher
        hash_file(sync_file)
    # record scan completion time
    sync_file.stime = utils.time_now()
    # save 
    session.add(sync_file)
    session.commit()


