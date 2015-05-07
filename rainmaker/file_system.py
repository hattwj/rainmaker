import os
import shutil

from .logger import create_log
log = create_log(__name__)

class FsActions(object):
    '''
        Take and log file system actions
    '''
    def mkdir(self,path):
        if os.path.isdir(path):
            log.info('[exists] %s' % path)
        else:
            os.mkdir(path)
            log.info('[created] %s' % path)

    def rmdir(self,path):
        if not os.path.isdir(path):
            log.info('[missing] %s' % path)
        else:
            shutil.rmtree(path)
            log.info('[deleted] %s' % path)
    
    def rm(self,path):
        if not os.path.exists(path):
            log.info('[missing] %s' % path)
        else:
            os.remove(path)
            log.info('[deleted] %s' % path)
    
    def write(self, path, content):
        if not os.path.exists(path):
            log.info('[created] %s' % path)
        else:
            log.info('[replaced] %s' % path)
        f = open( path, 'wb' )
        f.write( content )
        f.close()    

    def touch(self, path):
        if not os.path.exists(path):
            f = open( path, 'wb' )
            f.close()
            log.info('[created] %s' % path)

    def copy(self, p1, path):
        if not os.path.exists(path):
            log.info('[created] %s' % path)
        else:
            log.info('[replaced] %s' % path)
        shutil.copy(p1, path)

    def append(self, path, val):
        with open(path, "a") as myfile:
                myfile.write(val)
        log.info('[insert] %s' % path)

from threading import Lock
from rainmaker.db.serializers import FileParts
class DownloadManager():
    chunk_size = FileParts.chunk_size

    def __init__(self, host_file):
        self.file_size = host_file.file_size
        self.complete = False
        self.lock = Lock() 
        fparts = host_file.file_parts
        self.parts_needed = [idx for idx, v in fparts.iteritems()]

    @property
    def incoming_path(self):
        '''
            Temp path of file
        '''
        return self.path + '.part'

    @property
    def path(self):
        '''
            Target path of file
        '''
        return os.path.join(self.host_file.host.sync.path, self.host_file.rel_path)
    
    @property
    def path_dir(self):
        return os.path_dir(self.path)

    def gen_file(self):
        '''
            Generate blank file
        '''
        path = self.path
        if self.host_file.is_dir:
            if not os.isdir(path):
                os.mkdirs(path)
            self.complete = True
            return
        
        ipath = self.incoming_path
        
        if not os.is_dir(self.path_dir):
            os.make_dirs(self.path_dir)
        
        if os.path.exists(ipath):
            return
        
        with open(ipath, "wb") as out:
            out.truncate(self.file_size)
    
    def recv(self, pos, data):
        chunk_size = self.host_file.file_parts.pos_len(pos)
        chunk = self.chunks.get(pos)
        chunk = data if chunk is None else chunk + data
        if len(chunk) == chunk_size:
            self.check_part(pos, chunk)
            self.write_chunk(pos, chunk)

    def write_chunk(self, pos, data):
        with open(self.incoming_path, 'ab') as out:
            out.seek(pos*self.chunk_size)
            out.write(data)
            self.received_part(pos)

    def received_part(self, pos):
        self.parts_needed.remove(pos)
