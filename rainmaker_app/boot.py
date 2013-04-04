import os
import yaml

import app
import lib

class Rainmaker(object):
    did_init = False
    config = None
    logger = None
    templates = None
    profiles = None
    
    root = os.path.abspath(os.path.join(os.path.dirname(__file__)) )
    home_dir = os.path.expanduser('~')
    rain_dir = os.path.join(home_dir,'.rainmaker')
    log_path = os.path.join(rain_dir,'rainmaker.log')
    unison_dir = os.path.join(home_dir,'.unison')
    
    conf_dir=os.path.join(root,'conf')
    events_path = os.path.join(conf_dir,'events.yml')
    config_path = os.path.join(conf_dir,'config.yml')
    locale_dir = os.path.join(conf_dir,'locale') 

    def install(self):
        self.init_required()
        lib.tasks.install(self)
             
    def init_required(self):
        if self.config != None :
            return True
        self.do_init()
        return True

    def do_init(self):
        self.config = app.initialize.AppConfig(self)
        self.init_callbacks()
        self.logger = app.initialize.AppLogger(self)
        self.log = lib.logger.create()
        self.profiles = app.initialize.AppProfiles(self)
        self.callbacks.trigger('init')
        self.did_init = True
        return True

    def init_callbacks(self):
        f=open(self.events_path,'r')
        self.events = yaml.safe_load(f)
        f.close()
        self.callbacks = lib.Callbacks(self,self.events['app'])

    def run(loop=True):
        self.loop = app.initialize.AppLoop(self,loop)
