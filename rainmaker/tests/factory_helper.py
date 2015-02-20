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

def SyncFile(sync, count=1):
    ''' create file and return sync_file '''
    sync_files = []
    for x in range(0, count):
        path = Files(sync.path, 1)
        sync_file = db.SyncFile(sync=sync)
        sync_file.path = path
        sync_files.append(sync_file)
    if count==1:
        return sync_file
    return sync_files

