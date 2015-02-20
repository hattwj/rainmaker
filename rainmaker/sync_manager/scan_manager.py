import os
import hashlib
import zlib

from rainmaker.db.main import Sync, SyncFile, SyncPart
from rainmaker import utils

def hash_file(path, adler_f, md5_f, chunk_size=40000):
    ''' Full hash of file, make callback on each round '''
    offset = 0      # byte offset in file
    adler = 0       # adler32 rolling hash
    with open(path, 'rb') as fh:
        # For every chunk
        while True:
            # Get a chunk of file data
            data = fh.read(chunk_size)
            if not data:
                break # End of file
            adler = zlib.adler32(data, adler)
            # Is this the expected adler value?
            if not adler_f(adler, offset, len(data)):
                # nope, calculate the md5
                m = hashlib.md5()
                m.update(data)
                md5_f(m.hexdigest(), adler,  offset, len(data))
            # update offset
            offset += chunk_size
    return adler

def scan(session):
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
    ''' Scan a file, update if needed 
        - high      md5
        - medium    adler32
        - low       mtime, inode, ctime
    '''    
    def _adler_f(rolling_hash, offset, data_len):
        # check to see if digest in collection
        # if is: return True
        # if not: return False
        if sync_file.file_hash is None:
            return False
        return offset in parts and parts[offset].rolling_hash == rolling_hash
    
    def _md5_f(part_hash, rolling_hash, offset, part_len):
        '''
            if hash:
                set hash to none
                wipe all parts with offset greater than offset
            create and append new part
        '''
        if sync_file.file_hash is not None:
            sync_file.file_hash = None
            parts.clear()
            rparts = []
            for key, part in parts.items():
                if key >= offset:
                    parts.pop(key)
                    sync_file.sync_parts.remove(part)
        sync_part = SyncPart(part_hash=part_hash, part_len=part_len, 
            rolling_hash=rolling_hash, offset=offset)
        sync_file.sync_parts.append(sync_part)
    # Mark as deleted if is_dir
    if sync_file.is_dir and sync_file.id is not None:
        sync_file.stime_start = utils.time_now()
        sync_file.stime = utils.time_now()
        sync_file.does_exist = False
        session.add(sync_file)
        sync_file = SyncFile(
            sync_id = sync_file.sync_id, 
            rel_path = sync_file.rel_path)
    # start scan
    sync_file.stime_start = utils.time_now()
    sync_file.stime = 0
    sync_file.is_dir = False
    sync_file.does_exist = True
    # Check file state
    with open(sync_file.path, 'rb' ) as f:
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
    session.add(sync_file)
    session.commit()
    # load parts into dict for easy access
    parts = {}
    for part in sync_file.sync_parts:
        parts[part.offset] = part
    sync_file.file_hash = hash_file(sync_file.path, _adler_f, _md5_f)
    sync_file.stime = utils.time_now()
    session.add(sync_file)
    session.commit()

