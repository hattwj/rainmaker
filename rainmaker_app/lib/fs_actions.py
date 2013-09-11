import os
import shutil

from .logger import create as create_log

class FsActions(object):
    def __init__(self):
        self.log = create_log(self.__class__.__name__)

    def mkdir(self,path):
        if os.path.isdir(path):
            self.log.info('[exists] %s' % path)
        else:
            os.mkdir(path)
            self.log.info('[created] %s' % path)

    def rmdir(self,path):
        if not os.path.isdir(path):
            self.log.info('[missing] %s' % path)
        else:
            shutil.rmtree(path)
            self.log.info('[deleted] %s' % path)
    
    def rm(self,path):
        if not os.path.exists(path):
            self.log.info('[missing] %s' % path)
        else:
            os.remove(path)
            self.log.info('[deleted] %s' % path)
    
    def write(self, path, content):
        if not os.path.exists(path):
            self.log.info('[created] %s' % path)
        else:
            self.log.info('[replaced] %s'% path)
        f = open( path, 'wb' )
        f.write( content )
        f.close()

    

    def copy(self,p1,path):
        if not os.path.exists(path):
            self.log.info('[created] %s' % path)
        else:
            self.log.info('[replaced] %s'% path)
        shutil.copy(p1,path) 
