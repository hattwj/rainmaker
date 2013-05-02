from yaml import safe_load

from .path import which,current_user
from .logger import create  
from .callbacks import Callbacks
from .attrs_bag import AttrsBag

class RecordHooks(AttrsBag):
    
    def __init__(self,name=None):
        AttrsBag.__init__(self) 
        self.log = create(name)
        callbacks=[
            'init',
            'validate',
            'save',
            'delete'
        ]
        self.callbacks = Callbacks(self,callbacks)
        self.errors = []
        self.valid = None

    def validate(self,**kwargs):
        result = self.callbacks.trigger('validate',**kwargs)
        return result

    def delete(self,**kwargs):
        result = self.callbacks.trigger('delete',**kwargs)
        return result

    def save(self,**kwargs):
        result = self.callbacks.trigger('save',**kwargs)
        return result  
