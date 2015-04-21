import random
import os

import rainmaker.db.main as db
from rainmaker.file_system import FsActions
from rainmaker.main import Application
from rainmaker.sync_manager import scan_manager

fs = FsActions()
msize = 10**random.randint(0,10)

def Files(root, count=10, size=2):
    '''
        create many random files
        return their paths
    '''
    results = []
    fs.mkdir(root)
    for n in range(0, count):
        cur_path = os.path.join(root, str(random.random()) )
        with open(cur_path, 'w') as f:
            for x in range(0, size):
                f.write(str(random.randint(0,msize)))
        results.append(cur_path)
    if count==1:
        return cur_path
    return results

def Dirs(root, count=10):
    results = []
    for n in range(0, count):
        cur_path = os.path.join(root, str(random.random()) )
        fs.mkdir(cur_path)
        results.append(cur_path)
    if count==1:
        return cur_path
    return results

def Sync(count=1, fake=False):
    ''' create dir and return sync '''
    syncs = []

    for x in range(0, count):
        root = os.path.join(Application.user_root, str(random.random()))
        if not fake:
            fs.mkdir(root)
        sync = db.Sync()
        sync.path = root
        syncs.append(sync)
    if count==1:
        return sync
    return syncs
 
def SyncFile(sync, count, **kwargs):
    ''' create file and return sync_file '''
    sync_files = []
    fake = kwargs.pop('fake', False)
    for x in range(0, count):
        is_dir = kwargs.get('is_dir', bool(random.getrandbits(1)))
        if fake:
            path = os.path.join(sync.path, str(random.random()) )
        elif is_dir:
            path = Dirs(sync.path, 1) 
        else:
            path = Files(sync.path, 1)
        sync_file = db.SyncFile(**kwargs)
        if fake:
            if is_dir:
                sync_file.file_size = 0
            else:
                sync_file.file_size = random.randint(0, msize) 
        sync.sync_files.append(sync_file)
        sync_file.is_dir = is_dir
        sync_file.sync_id = sync.id
        sync_file.path = path
        sync_file.does_exist=True
        sync_files.append(sync_file)
    if count == 1:
        return sync_file
    return sync_files

def SyncPart(sync_file, **kwargs):
    ''' create file and return host_file '''
    sync_parts = []
    for x in range(0, sync_file.file_size, scan_manager.chunk_size):
        sync_part = db.SyncPart(**kwargs)
        sync_part.part_offset = x
        sync_part.part_len = scan_manager.chunk_size
        if sync_part.part_len + x > sync_file.file_size:
            sync_part.part_len = sync_file.file_size - x
        sync_part.part_hash = str(random.randint(0,100000))
        sync_part.rolling_hash = random.randint(0,100000)
        sync_file.sync_parts.append(sync_part)
        sync_parts.append(sync_part)
    return sync_parts


def Host(sync, count, **kwargs):
    ''' create file and return host_file '''
    hosts = []
    for x in range(0, count):
        host = db.Host(**kwargs)
        host.pubkey = str(random.random())
        sync.hosts.append(host)
        hosts.append(host)
    if count == 1:
        return host
    return hosts


def HostFile(host, count, **kwargs):
    ''' create file and return host_file '''
    host_files = []
    for x in range(0, count):
        
        host_file = db.HostFile(**kwargs)
        if host_file.is_dir is None:
            host_file.is_dir = bool(random.getrandbits(1))
        host_file.does_exist=True
        host_file.rel_path = str(random.random())
        if host_file.is_dir:
            host_file.file_size = 0
        else:
            host_file.file_size = random.randint(0,100000)
        host_file.host = host
        host_file.host_id = host.id
        host_file.rid = x
        host_files.append(host_file)
    if count == 1:
        return host_file
    return host_files

def HostPart(host_file):
    ''' create file and return host_file '''
    for x in range(0, host_file.file_size, scan_manager.chunk_size):
        host_part = db.HostPart()
        host_part.part_offset = x
        host_part.part_len = scan_manager.chunk_size
        if host_part.part_len + x > host_file.file_size:
            host_part.part_len = host_file.file_size - x
        host_part.part_hash = str(random.randint(0,100000))
        host_part.rolling_hash = random.randint(0,100000)
        host_file.host_parts.append(host_part)
    return host_file.host_parts

def SyncRand(count=10):
    sync = Sync(1, fake=True)
    host = Host(sync, 1)
    sync_files = SyncFile(sync, count, is_dir=False, fake=True)
    host_files = HostFile(host, count, is_dir=False)
    for sf in sync_files:
        SyncPart(sf)
    for hf in host_files:
        HostPart(hf)
    return sync

