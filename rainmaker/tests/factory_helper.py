import random
import os

import rainmaker.db.main as db
from rainmaker.db import serializers

from rainmaker.utils import rand_str
from rainmaker.file_system import FsActions
from rainmaker.main import Application
from rainmaker.sync_manager import scan_manager


fs = FsActions()
msize = 10**6

def FileParts(a_file):
    fsize = a_file.file_size
    fp = serializers.FileParts()
    pos = 0
    
    while pos*fp.chunk_size < fsize:
        fp.put(pos, 12345, '34567890')
        pos += 1
    a_file.fparts = fp.dump()
    
def Files(root, count=10):
    '''
        create many random files
        return their paths
    '''
    results = []
    fs.mkdir(root)
    for n in range(0, count):
        cur_path = os.path.join(root, str(random.randint(0, msize)) )
        data = rand_str(random.randint(1, msize))
        with open(cur_path, 'w') as f:
            f.write(data)
        results.append(cur_path)
    if count==1:
        return cur_path
    return results

def Dirs(root, count=10):
    results = []
    for n in range(0, count):
        cur_path = os.path.join(root, str(random.randint(0, msize)) )
        fs.mkdir(cur_path)
        results.append(cur_path)
    if count==1:
        return cur_path
    return results

def Sync(**kwargs):
    ''' create dir and return sync '''
    syncs = []
    count = kwargs.pop('count', 1)
    fake = kwargs.pop('fake', None)
    path = kwargs.pop('path', Application.user_dir)
    for x in range(0, count):
        root = os.path.join(path, str(random.randint(0, msize*99999999)))
        if fake is None:
            fs.mkdir(root)
        sync = db.Sync(**kwargs)
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
            path = os.path.join(sync.path, str(random.randint(0, msize*9999999)) )
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
                FileParts(sync_file)
        sync.sync_files.append(sync_file)
        sync_file.is_dir = is_dir
        sync_file.sync_id = sync.id
        sync_file.path = path
        sync_file.does_exist=True
        sync_files.append(sync_file)
    if count == 1:
        return sync_file
    return sync_files

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
            FileParts(host_file)
        host_file.host = host
        host_file.host_id = host.id
        host_file.rid = x
        host_files.append(host_file)
    if count == 1:
        return host_file
    return host_files

def HostRand(sync, count=10):
    host = Host(sync, 1)
    host_files = HostFile(host, count, is_dir=False)
    return host

def SyncRand(**kwargs):
    kwargs['fake'] = kwargs.get('fake', True)
    kwargs['count'] = kwargs.get('count', 1)
    file_count = kwargs.pop('file_count', 10)
    sync = Sync(**kwargs)
    sync_files = SyncFile(sync, file_count, is_dir=False, fake=kwargs['fake'])
    return sync

import rainmaker.tests.test_helper
import rainmaker.tox.main
def ToxServers(sess):
    tox_html = rainmaker.tests.test_helper.load('fixtures/tox_nodes.html')
    return rainmaker.tox.main.html_to_tox_servers(sess, tox_html)

