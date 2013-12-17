from copy import deepcopy
from pipes import quote                 #repr
from .record_script import RecordScript

def convert_dict(a_dict):
    ''' convert a dict with . keys into a nested dict '''
    result = {}
    for k, v in a_dict.iteritems():
        ksplit = k.split('.')
        cur = result
        for attr in ksplit[:-1]:
            if not attr in cur.keys():
                cur[attr] = {}
            elif not isinstance( cur[attr], dict):
                cur[attr] = {}
            cur = cur[attr]
        cur[ksplit[-1]] = v
    return result

def nested_merge(old, new):
    ''' perform nested merge on two dicts '''
    for k, v in new.iteritems():
        # recurse on nested dict
        if isinstance(v, dict):
            if not k in old.keys():
                old[k] = {}
            nested_merge(old[k], new[k])
            continue
        old[k]=v
    return old

class AttrsBag(object):
    
    def __init__(self,attrs=None):
        object.__setattr__(self,'attrs', {} )
        object.__setattr__(self,'script', RecordScript())
        
        # return if no keys sent by default
        if not attrs: return
        self.add_attrs(attrs)
    
    def add_attrs(self,a_dict):
        ''' merge with dict '''
        if not a_dict:
            return
        # prevent accidental byref
        a_dict = convert_dict( a_dict )
        attrs = object.__getattribute__(self,'attrs') 
        attrs = nested_merge( attrs, a_dict)
        object.__setattr__(self,'attrs', attrs )
        attrs = object.__getattribute__(self,'attrs') 
        # update script attributes
        self.script.attrs_update( attrs )
    
    def __getattribute__(self,name):
        try:
            attrs = object.__getattribute__(self,'attrs')
        except AttributeError:
            attrs = None
        if attrs and name in attrs:
            val = attrs[name]
            if isinstance(val, str):
                return self.subst( val )
            elif isinstance(val, list):
                return [self.subst(v) for v in val]
            elif isinstance(val, dict):
                return {k:self.subst(v) for k, v in val.iteritems() }
            else:
                return val
        else:
            return object.__getattribute__(self,name)
    
    def __setattr__(self,name,val):
        attrs = self.attrs
        if name in attrs:
            attrs[name]=val
            # update script attributes
            self.script.attrs_update( attrs )
        else:
            object.__setattr__(self,name, val )
    
    def __repr__(self):
        result = '<%s ' % self.__class__.__name__
        for k, v in object.__getattribute__(self,'attrs').iteritems():
            result += ' %s=>%s' % (k, repr(v)) 
        result += '>'
        return result

    def get(self, name):
        ''' Get data and do not translate '''
        try:
            attrs = object.__getattribute__(self,'attrs')
        except AttributeError:
            attrs = None
        if attrs and name in attrs:
            return attrs[name]

    # substitute val with optional attrs dict
    def subst(self, val, attrs=None):
        return self.script.subst(val,attrs)

