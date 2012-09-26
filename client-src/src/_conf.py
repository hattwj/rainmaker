#!/usr/bin/python
"""
This file is part of Rainmaker.

    Rainmaker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Rainmaker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Rainmaker.  If not, see <http://www.gnu.org/licenses/>.
"""

import _path

import yaml
import sys
import os
import logging
import collections


# a collection to hold rainmakerdata classes
class RainmakerDataCollection(collections.MutableMapping):
    def __init__(self,data):
        self.data=data
        self.d={}
            
        for k in self.data:
            if self.data[k]['type']=='rainmaker_data':
                self.d[k]=RainmakerData(self.data[k])

    def __getitem__(self,key):
        return self.d[key]

    def __setitem__(self,key,value):
        if value.__class__.__name__==RainmakerData.__name__:
            self.d[key]=value.d
            self.data[key]=value.data
        else:
            print 'error'
            sys.exit()
    def __delitem__(self,key):
        del self.data[key]
        if key in self.d:
            del self.d[key]
    def __iter__(self):
        return iter(self.data)
    def __len__(self):
        return len(self.data)

import re
# dict with keys - type,val,desc,default
class RainmakerData(collections.MutableMapping):

    def __init__(self,data=None):
        self.log = logging.getLogger('data')
        self.re = re.compile('\?([a-z_]+)\?')
        self.data=data or self.new_data()
        self.d={}
            
        for k in self.data['val']:
            if data['val'][k]['type']=='rainmaker_data':
                self.d[k]=RainmakerData(self.data['val'][k])

    # set val=default for all keys recursively
    def set_default(self):
        for k in self:
            if k in self.d:
                self.d[k].set_default()
            else:
                self[k]=self.meta(k)['default']
                if self.meta(k)['type'] != 'arr':
                    self[k]=self.subst(self[k])
    # eval all values and substitute them
    def subst_all(self):
        self.read_only=True
        for k in self:
            if k in self.d:
                self.d[k].subst_all()
            elif self.meta(k)['type']=='arr':
                #print 'subst for arr not implemented'
                next
            else:
                self[k]=self.subst(self[k])

            if self.meta(k)['type']=='localpath':
                self[k]=os.path.abspath( os.path.expanduser(self[k]) )

    #substitute values between variables 
    def subst(self,val):
        if val is None or val ==False or val==True:
            return val
        val = str(val)
        m=self.re.findall(val)
        c = 0
        while m and c<5:
            c+=1
            for g in m:
                #print 'group: %s' % g
                substr=None
                if g in self:
                    substr= self[g]
                else:
                    if hasattr(_path, 'cmd_%s' % g):
                        substr=getattr(_path,'cmd_%s' % g)() 
                
                if substr:
                    val=val.replace('?%s?' % g, str(substr))
                else:
                    pass #print 'raise substr error'
            m=self.re.findall(val)

        return val

    # allow printing like a normal dictionary 
    def __repr__(self):
        return repr(self.data)

    def __getitem__(self,key):

        if key in self.d:
            return self.d[key]
        else:
            return self.data['val'][key]['val']

    def __setitem__(self,key,value):
        #nest a rainmakerdata item
        if value.__class__.__name__==self.__class__.__name__:
            self.d[key]=value.d
            self.data[key]=value.data
        else:
            #validate new val
            if self.validate(self.data['val'][key],value):
                self.data['val'][key]['val']=value
            else:
                self.log.error('invalid data: %s - %s' % ( str(key), str(value) ))

    def new_data(self,val=None):
        return {'val':val,'type':'rainmaker_data','desc':None,'default':None}
    
    def meta(self,key):
        return self.data['val'][key]

    def __delitem__(self,key):
        del self.data['val'][key]
        if key in self.d:
            del self.d[key]
    def __iter__(self):
        return iter(self.data['val'])
    def __len__(self):
        return len(self.data)

    def has_key(self,key):
        return self.data.has_key(key)

    def validate(self,q,val):
        if q['type']=='str':
            return len(str(val or ''))>0
        elif q['type']=='int':
            return 65536>=int(val)>0
        elif q['type']=='port':
            return 65536>=int(val)>0
        elif q['type']=='host':
            return len(str(val))>0 
        elif q['type']=='arr':
            return isinstance(val,list)
        elif q['type']=='localpath':
            return len(str(val))>0
        elif q['type']=='bool':
            if val == False or val == True: 
                return True
            if val.lower()=='false' or val.lower()=='f' or val.lower()=='true' or val.lower()=='t':
                return True
        return False
    
    @staticmethod
    def new(vals):
        result={}
        for key in data:
            val=data[key]
            result[key] = RainmakerData({'val':val,'type':'rainmaker_data','desc':None,'default':None})
        return result

#config class
class RainmakerConfig(dict):
    profiles = {}
    templates = {}
    profiles_data={}
    def __init__(self):        
        self.log = logging.getLogger('config')
        self.home = os.path.expanduser('~')
        self.rain_dir = os.path.join(self.home,'.rainmaker')
        self.log_f='rainmaker.log'
        self.log_path=os.path.join(self.rain_dir,self.log_f)
        self.unison_dir = os.path.join(self.home,'.unison')
        self.profiles_f = 'profiles.yml'
        self.profiles_path=os.path.join(self.rain_dir,self.profiles_f)
        self.config_f = 'config.yml'
        self.config_path=os.path.join(self.rain_dir,self.config_f)
        self.app_dir = os.path.abspath(os.path.join(sys.path[0],'..'))
        self.app_conf_dir=os.path.join(self.app_dir,'conf')
        self.config_path_ro=os.path.join(self.app_dir,'conf',self.config_f)
               
        if not os.path.isdir(self.rain_dir):
            os.mkdir(self.rain_dir)
        if not os.path.isdir(self.unison_dir):
            os.mkdir(self.unison_dir)

        if not os.path.isfile(self.config_path):
            if not os.path.isfile(self.config_path_ro):
                self.log.error( 'Unable to find config file' )
                sys.exit()
            self.config_path=self.config_path_ro

        f = open(self.config_path,'r')
        self.config_data = yaml.safe_load( f )
        f.close()
                
        self.templates=RainmakerDataCollection(self.config_data['templates'])

        if os.path.isfile(self.profiles_path):
            f = open(self.profiles_path,'r')
            self.profiles_data = yaml.safe_load( f )
            f.close()

        if self.profiles_data == None:
            self.profiles_data={}
        
        self.profiles=RainmakerDataCollection(self.profiles_data)

    def __getitem__(self, key):
        val = self.config_data.__getitem__( key)
        return val

    def __setitem__(self, key, val):
        self.config_data.__setitem__( key, val)

    def save_profiles(self):
        f = open(self.profiles_path,'w')
        yaml.safe_dump(self.profiles_data, f)
        f.close()
        self.log.info('Changes saved to: %s ' % self.profiles_path)
        return

    def delete_profile(self,k):
        if not k in self.profiles:
            self.log.error('Unknown profile, can\'t delete: %s' % k)
            return
        
        p=self.profiles.pop(k)

        do_prf_del=p['profile_type']=='rainmaker_unison'

        if do_prf_del:
            path =  os.path.join(self.unison_dir, '%s.prf' % p['prf'] )
            if os.path.isfile(path):
                self.log.info( 'Deleting unison profile: %s' % path )
                os.remove(path)
            else:
                self.log.info( 'Unable to delete unison profile - %s' % path )
        did_delete=True
        self.log.info('Removed profile: %s' % k)

        if did_delete:
            self.save_profiles()
        else:
            self.log.warn( 'No changes to save' )

    def find(self,fname):
        paths=[
            self.rain_dir,
            self.unison_dir,
            self.app_dir,
            self.app_conf_dir
        ]

        for path in paths:
            result = os.path.join(path,fname)
            if os.path.isfile(result):
                return result
        return None

    # Test config yaml file for misconfiguration and return results
    def test(self):
         # return false if everything passed
         # return array of error codes on fail 
         self.log.warn('profile testing not implemented')
         pass

