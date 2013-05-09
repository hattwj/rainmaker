from copy import deepcopy
from .record_script import RecordScript

class AttrsBag(object):
    
    def __init__(self,attrs={},dict_to_obj=False):
        object.__setattr__(self,'attrs', {} )
        object.__setattr__(self,'script', RecordScript())
        
        # load and prevent accidental byref 
        if dict_to_obj:
             self.dict_to_obj( deepcopy(attrs) )
        else:
             self.add_attrs( deepcopy(attrs) )
    
    def dict_to_obj(self,attrs):
        ''' Merge with dict to create methods '''
        new_attrs = {}
        for k,v in attrs.iteritems():
            new_attrs = self.new_attr(k,v,k,k,new_attrs)
        self.add_attrs(new_attrs)

    def add_attrs(self,a_dict):
        ''' merge with dict '''
        # prevent accidental byref
        a_dict=deepcopy(a_dict)
        attrs = object.__getattribute__(self,'attrs') 
        object.__setattr__(self,'attrs', dict(attrs.items()+a_dict.items()) )
     
    def new_attr(self,name,default,type,desc,attrs={}):
        ''' return attr prototype'''
        attrs[name]={'default':default,'desc':desc,'type':type}
        return attrs

    def __getattribute__(self,name):
        try:
            attrs = object.__getattribute__(self,'attrs')
        except AttributeError:
            attrs = None
        if attrs and name in attrs:
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
    
    def attr_subst(self,name,val=None):
        val = getattr(self,name) if not val else val 
        return setattr(self,name,self.subst(val))

    # substitute val template with attrs dict
    def subst(self, val, attrs={}):
        self.script.attrs_update( self.attrs_dump() )
        return self.script.subst(val,attrs)


