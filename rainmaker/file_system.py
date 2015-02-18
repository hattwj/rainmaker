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

