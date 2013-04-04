from copy import deepcopy

class AttrsBag(object):
    
    def __init__(self,attrs={}):
        # prevent accidental byref 
        attrs = deepcopy(attrs)
        object.__setattr__(self,'attrs', attrs )
    
    def add_attrs(self,a_dict):
        # prevent accidental byref
        a_dict=deepcopy(a_dict)
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
    
    def attr_type(self,val):
        return self.attrs[val]['type']
    def attr_default(self,val):
        return self.attrs[val]['default']
    def attr_val(self,val):
        return self.__getattribute__(val)
    def attr_desc(self,val):
        return self.attrs[val]['desc']
    def attr_validate(self,val):
        return True
        
    def attr_is(self,key,val):
        if val in self.attrs and self.attrs[val]['type']==key:
            return True
        return False
    
