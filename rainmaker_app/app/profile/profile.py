from os import remove

from yaml import safe_dump,safe_load
import re

from rainmaker_app.lib import RecordHooks
from rainmaker_app.lib.conf import load

class Profile(RecordHooks):

    def __init__(self,data={},vals=None,path=None):
        RecordHooks.__init__(self,self.__class__.__name__)
        self.add_attrs(data)
        self.dict_to_obj({'path':path})
        if vals:
            for k,v in vals.iteritems():
                setattr(self,k,v)
        self.callbacks.add('get_events')
        self.callbacks.register('delete',self.on_delete)
        self.callbacks.register('save',self.on_save)
        self.callbacks.register('validate',self.on_validate)

    def on_validate(self, **kwargs):
        return True

    def on_save(self,**kwargs):
        if not self.path:
            return False
        f = open(self.path,'w')
        
        self.guid = self.subst(self.guid)
        safe_dump(self.attrs_dump_key('val'), f,default_flow_style=False)
        f.close()
        self.log.info('Changes saved to: %s ' % self.path)
        return True

    def on_delete(self,**kwargs):
        if not self.path:
            return False
        remove(self.path)
        return True

    def on_before_save(self,**kwargs):
        # set guid
        if self.guid == None:
            self.guid = _lib.rand_str(10)

