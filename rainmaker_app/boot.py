import os
import yaml

import tasks
from .conf import load
from .lib import logger, path, cli, Callbacks, AttrsBag
from .app import initialize

class Rainmaker(AttrsBag):
    event_handlers = None
    profiles = None
    callbacks = None

    def __init__(self):
        AttrsBag.__init__(self, load('rainmaker.yml') )
        self.callbacks = Callbacks(self,['init','shutdown'])
   
    def set_user_dir(self,path):
        self.user_dir = os.path.abspath(os.path.expanduser(path))
        self.profiles_dir = os.path.join(self.user_dir,'profiles')
        self.tmp_dir = os.path.join(self.user_dir,'tmp')
        self.log_path = os.path.join(self.user_dir,'rainmaker.log') 
        
    # called after parser run to complete init sequence
    def init(self):
        self.log = logger.create(self.__class__.__name__)
        logger.log_to_file(self.log_path,'') 
        self.callbacks.run('before_init')
        tasks.install(self.user_dir)
        self.config = load('rainmaker.yml')
        self.profiles = initialize.AppProfiles(self.user_dir)
        self.loop = initialize.AppLoop(self.tmp_dir)
        self.callbacks.run('init')
        self.callbacks.run('after_init')
        return True
    
    # the application will now shut down
    # - trigger related shutdown events
    def shutdown(self):
        if self.loop:
            self.loop.shutdown()
        self.callbacks.trigger('shutdown')
