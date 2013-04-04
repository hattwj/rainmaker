from os import remove
from string import Template
from yaml import safe_dump

from lib import RecordHooks
import app

from conf.model import unison_profile
from unison_handler import UnisonHandler

class UnisonProfile(RecordHooks):

    def __init__(self,data={}):
        RecordHooks.__init__(self,'profile')
        self.path=None
        attrs = unison_profile.attrs
        self.add_attrs(attrs)
        self.add_attrs(data)
        self.handler = UnisonHandler()
        self.callbacks.register('delete',self.on_delete)
        self.callbacks.register('save',self.on_save)
        self.callbacks.register('validate',self.on_validate)
    
    def subsititute(self, val):
        pass
    def on_validate(self, **kwargs):
        return True

    def on_save(self,**kwargs):
        f = open(self.path,'w')
        safe_dump(self.attrs_dump(), f)
        f.close()
        self.log.info('Changes saved to: %s ' % self.path)
        return True

    def on_delete(self,**kwargs):
        remove(self.path)

    def on_before_save(self,**kwargs):
        # set guid
        if self.guid == None:
            self.guid = _lib.rand_str(10)
