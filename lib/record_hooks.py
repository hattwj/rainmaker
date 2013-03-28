from string import Formatter
from yaml import safe_load

from lib.path import which,current_user
from record_script import RecordScript

import lib

class RecordHooks(object):
    
    def __init__(self,name=None):
        object.__setattr__(self,'attrs', {} )
        self._formatter = Formatter()
        self.log = lib.logger.create(self.__class__.__name__)
        callbacks=[
            'init',
            'validate',
            'save',
            'delete'
        ]
        self.callbacks = lib.Callbacks(self,callbacks)
        self.errors = []
        self.valid = None
        self.script = RecordScript()

    def add_attrs(self,a_dict):
        attrs = object.__getattribute__(self,'attrs') 
        object.__setattr__(self,'attrs', dict(attrs.items()+a_dict.items()) )

    def __getattribute__(self,name):
        attrs = object.__getattribute__(self,'attrs') 
        if name in attrs:
            return attrs[name]['val'] if 'val' in attrs[name] else attrs[name]['default']
        else:
            return object.__getattribute__(self,name)
    
    def __setattr__(self,name,val):
        attrs = self.attrs
        if name in attrs:
            attrs[name]['val']=val
        else:
            object.__setattr__(self,name, val )            
    
    # dump val or default, whichever exists 
    def attrs_dump(self):
        return dict( 
            self.attrs_dump_key('default').items() + 
            self.attrs_dump_key().items()
        )
    
    # dump just the vals
    def attrs_dump_key(self,key='val'):
        attrs = self.attrs
        result = {}
        for k in attrs:
            if key in attrs[k]:
                result[k] = attrs[k][key]
        return result
    
    def validate(self,**kwargs):
        result = self.callbacks.trigger('validate',**kwargs)
        return result

    def delete(self,**kwargs):
        result = self.callbacks.trigger('delete',**kwargs)
        return result

    def save(self,**kwargs):
        result = self.callbacks.trigger('save',**kwargs)
        return result 
    
    def attr_type(self,val):
        return self.attrs[val]['type']

    def attr_desc(self,val):
        return self.attrs[val]['desc']
    
    def attr_is(self,key,val):
        if val in self.attrs and self.attrs[val]['type']==key:
            return True
        return False
    
    # substitute val template with attrs dict
    def subst(self, val, attrs={}):
        self.script.attrs_update( self.attrs_dump() )
        return self.script.subst(val,attrs)
