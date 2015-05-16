'''
    Primary Entry point for application, configuration, init, stop
'''
import os

import rainmaker
import rainmaker.db
import rainmaker.tox
import rainmaker.tasks
import rainmaker.file_system
import rainmaker.file_server

from rainmaker.db.main import init_db
from rainmaker.tox.main import init_tox
from rainmaker.sync_manager.main import init_sync

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

class ApplicationClass(object):
    version = rainmaker.version

    # Application singletons go here
    fs_log = rainmaker.file_system.FsActions()
    file_server = rainmaker.file_server.FileServer()    

    device_name = 'unknown'

    # Application paths
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..') )
    conf_root = os.path.abspath(os.path.join(root,'conf'))
    
    # User config paths
    user_dir = os.path.join(os.path.expanduser('~'), '.config', 'rainmaker')
    db_name = 'rainmaker.sqlite'
    conf_name = 'config.yml'
    
    # search paths
    paths = [user_dir, conf_root]
    
    # runtime flags
    start_console = False
    start_tox = True
    stopping = False

    def load(self, **kwargs):
        # accepts kwargs to configure
        for k, v in kwargs.items():
            setattr(self, k, v)
     
    @property
    def db_path(self):
        return os.path.join(self.user_dir, self.db_name)
    
    @property
    def user_conf_path(self):
        return os.path.join(self.user_dir, self.conf_name)
    
    @property
    def root_conf_path(self):
        return os.path.join(self.root, 'conf', self.conf_name)

    def autorun(self):
        log.info("Starting rainmaker version: %s" % self.version)
        log.info('Checking installation...')
        # create user's config dir
        if not os.path.isdir(self.user_dir):
            did_install = True
            self.fs_log.mkdir(self.user_dir) 
            self.fs_log.touch(self.db_path)
    
        log.info('Initializing db...') 
        self.db = init_db(self.db_path)
    
        log.info('Configuring Tox...')
        init_tox(self.db)
    
        log.info('Initializing Sync Managers...')
        init_sync(self.db)

Application = ApplicationClass()
