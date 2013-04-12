import os
import yaml


from .conf import load
from .lib import logger, path, cli, tasks, Callbacks
from .app import initialize

class Rainmaker(object):
    event_handlers = None
    profiles = None
    callbacks = None

    root = os.path.abspath(os.path.join(os.path.dirname(__file__)) )
    home_dir = os.path.expanduser('~')
    rain_dir = os.path.join(home_dir,'.rainmaker')
    log_path = os.path.join(rain_dir,'rainmaker.log') 
    log_level = 'info'
    log_style='%(name)-12s %(levelname)-8s %(message)s'
    
    conf_dir=os.path.join(root,'conf')
    events_path = os.path.join(rain_dir,'events.yml')
    config_path = os.path.join(conf_dir,'config.yml')

    def __init__(self):
        self.callbacks = Callbacks(self,['init','shutdown'])
        self.log = logger.create(self.__class__.__name__)
    
    # called after parser run to complete init sequence
    def init(self):
        self.callbacks.run('before_init')
        tasks.install(self.rain_dir)
        self.config = load('rainmaker.yml')
        self.profiles = initialize.AppProfiles(self)
        self.loop = initialize.AppLoop(self)
        self.callbacks.run('init')
        self.callbacks.run('after_init')
        return True
    
    # dir of user data folder
    def profiles_dir(self,arg=None):
        return os.path.join(self.rain_dir,'profiles',arg)

    # the application will now shut down
    # - trigger related shutdown events
    def shutdown(self):
        self.callbacks.trigger('shutdown')
