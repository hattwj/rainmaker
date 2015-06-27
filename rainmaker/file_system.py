import os
import shutil

from .logger import create_log
log = create_log(__name__)

import hashlib
import zlib

chunk_size = 200000

def hash_chunk(chunk):
    m = hashlib.md5()
    m.update(chunk)
    return m.hexdigest()

def hash_file(sync_file, offset=0, n=0):
    ''' Full hash of file, make callback on each round '''
    parts = sync_file.file_parts
    chunk_size = parts.chunk_size
    adler = parts.get_adler(offset)
    with open(sync_file.path, 'rb') as fh:
        if offset:
            fh.seek(offset*chunk_size)
        # For every chunk
        while True:
            # Get a chunk of file data
            data = fh.read(offset*chunk_size)
            if not data:
                break # End of file
            # force sign of adler to signed int
            adler = zlib.adler32(data, adler) & 0xffffffff
            # Is this the expected adler value?
            if parts.get_adler(offset) != adler:
                # nope, calculate the md5
                parts.put(offset, adler, hash_chunk(data))
            # update part_offset
            offset += 1
            # break if we've reached zero
            n += 1
            if n == offset:
                break
    scan_len = chunk_size*offset + len(data)
    return (adler, scan_len)

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
        else:
            log.info('[exists] %s' % path)

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

