import random                           #cmd
from string import lowercase, digits, Formatter #cmd rand
from yaml import safe_load              #parser
from pipes import quote                 #cmd
from os.path import abspath,basename,expanduser  #cmd

from .path import which,current_user    #cmd

#from IPython.core.debugger import Tracer

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

class RecordScript(object):
    ''' RecordScipt: The active yaml templating dsl ''' 
    def __init__(self,attrs={},depth=3):
        #log = create(self.__class__.__name__)
        self.attrs=attrs
        self._formatter = Formatter() 
    
    # optionally remove flags from val 
    def remove_flags(self,val):
        for tup in self._formatter.parse(val):
            if not tup[1]:
                continue
            key = tup[1]
            rep_key = "${%s}" % ':'.join([key,tup[2]]) if tup[2] else "${%s}" % key
            val = val.replace(rep_key,'')
        return val

    # add/update attrs dict 
    def attrs_update(self, attrs):
        self.attrs = nested_merge(self.attrs, attrs)
     
    # substitute val template with attrs dict
    def subst(self, val, attrs=None,times=7,search_paths=[]):
        ''' parse string '''
        if val == None or isinstance(val, int) or isinstance(val, bool):
            return val
        result = val
        has_flags = False
        if attrs:
            attrs = dict( self.attrs.items() + attrs.items() )
        else:
            attrs = self.attrs
        #print attrs
        
        # get tuple of values for every key in string        
        for tup in self._formatter.parse(val):
            # next if no flags
            if tup[1] == None:
                continue
            
            #print tup
            
            # process tuple of flags - immutable array -
            has_flags=True
            key = tup[1]
            cmd_key = "__cmd_%s__" % key
            rep_key = "${%s}" % ':'.join([key,tup[2]]) if tup[2] else "${%s}" % key
            
            # Check to see if the string references another key in the attrs
            match,rep_val = self.search(key,attrs,search_paths)

            # get cmd if exists in this class
            cmd = getattr(self,cmd_key) if hasattr(self,cmd_key) else None
            # execute command if one is present and the command
            # doesn't have an override attribute set
            if cmd and not match:
                #log.debug("cmd: %s" % cmd_key)
                data = safe_load( tup[2] ) if tup[2] else None
                if isinstance(data,dict):
                    rep_val = cmd(attrs,search_paths,**data)
                elif isinstance(data,list): 
                    rep_val = cmd(attrs,search_paths,*data)
                elif data != None:
                    rep_val = cmd(attrs,search_paths,data)
                else:
                    rep_val = cmd(attrs)
            elif match:
                pass
            else:
                raise KeyError( [key,search_paths,attrs] )    
            if rep_val==None or not rep_key:
                #log.warn("subst missing val or key:\n\tval=%s\n\tkey=%s" % (rep_val,rep_key))
                continue
            if isinstance(rep_val,list):
                rep_val = ''.join(rep_val)
            elif rep_val == False:
                rep_val = ''
            result = result.replace(rep_key,str(rep_val),1)
        if times >= 1 and has_flags:
            result = self.subst(result,attrs,times-1,search_paths)
        else:
            pass
            #log.debug("output: %s" % result)
        return result

    def search(self,key_str,attrs,paths=[]):
        ''' search attrs for a value in several places '''
        if key_str in attrs:
            return [key_str,attrs[key_str]]
        keys = key_str.split('.')
        match = False
        val = None
        for path in paths+['']:
            path_arr = path.split('.') + keys
            match,val = self.get(path_arr,attrs)
            if match:
                break
        return [match,val]
    
    def get(self,arr,attrs):
        ''' Get a value from nest of dict/arrays '''
        path=[]
        val = attrs
        for k in arr:
            if k == '':
                continue
            if isinstance(val,list):
                k=int(k)
            try:
                val=val[k]
                path.append(str(k))
            except KeyError:
                path = None
                break
        path = path if path else None
        val = val if path else None
        return [path,val]

    def __cmd_for_each__(self,attrs,search_paths,key,val,elem_key=None):
        result = []
        xattrs = None
        key = self.subst(key,attrs)
        for elem in attrs[key]:
            # nest elem in dict if elem_key
            elem = {elem_key : elem} if elem_key else elem
            result.append( self.subst(val,elem,search_paths=search_paths) )
        return result
    
    def __cmd_quote__(self,attrs,search_paths,val):
        ''' Quote string'''
        return quote(self.subst(val,attrs,search_paths=search_paths))

    def __cmd_yaml__(self,attrs,search_paths,val):
        ''' return yaml object '''
        return safe_load(val)

    def __cmd_which__(self,attrs,search_paths,val):
        ''' search path for executable '''
        return which(self.subst(val,attrs,search_paths=search_paths))

    def __cmd_current_user__(self,attrs):
        ''' return name of current user '''
        return current_user()

    def __cmd_abspath__(self,attrs,search_paths,val):
        ''' return abspath '''
        return abspath(expanduser(self.subst(val,attrs,search_paths=search_paths)))
    
    def __cmd_basename__(self,attrs,search_paths,val):
        ''' return abspath '''
        return basename(self.subst(val,attrs,search_paths=search_paths))

    def __cmd_rand__(self,attrs,search_paths,val):
        ''' rand string of length val'''
        count=int(val)
        choices=lowercase+digits 
        return ''.join(random.choice(choices) for x in range(count))
