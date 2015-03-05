import random
import os

import rainmaker.db.main as db
from rainmaker.file_system import FsActions
from rainmaker.main import Application

fs = FsActions()

def Files(root, count=10, size=2):
    '''
        create many random files
        return their paths
    '''
    results = []
    fs.mkdir(root)
    msize = 10**random.randint(0,100)
    for n in range(0, count):
        cur_path = os.path.join(root, str(random.random()) )
        with open(cur_path, 'w') as f:
            for x in range(0, size):
                f.write(str(random.randint(0,msize))*1000)
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

def Sync(count=1):
    ''' create dir and return sync '''
    syncs = []
    for x in range(0, count):
        root = os.path.join(Application.user_root, str(random.random()))
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
    for x in range(0, count):
        path = Files(sync.path, 1)
        sync_file = db.SyncFile(**kwargs)
        sync_file.sync = sync
        sync_file.sync_id = sync.id
        sync_file.path = path
        sync_file.does_exist=True
        sync_files.append(sync_file)
    if count == 1:
        return sync_file
    return sync_files


def HostFile(host, count, **kwargs):
    ''' create file and return host_file '''
    host_files = []
    for x in range(0, count):
        host_file = db.HostFile(**kwargs)
        host_file.does_exist=True
        host_file.rel_path = str(random.random())
        host_file.is_dir = bool(random.getrandbits(1))
        if not host_file.is_dir:
            host_file.file_size = random.randint(0,100000)
        host_file.host = host
        host_file.host_id = host.id
        host_file.rid = x
        host_files.append(host_file)
    if count == 1:
        return host_file
    return host_files

