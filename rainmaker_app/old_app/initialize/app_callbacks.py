import yaml

from rainmaker_app.lib.conf import load
from rainmaker_app.lib.callbacks import Callbacks

class AppCallbacks(object):
    def __init__(self,parent):
        events = load('events.yml')
        parent.callbacks=Callbacks(parent,['init'])
