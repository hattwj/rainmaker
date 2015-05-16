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


class Application(object):
    version = rainmaker.version
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

    def __init__(self, **kwargs):
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

