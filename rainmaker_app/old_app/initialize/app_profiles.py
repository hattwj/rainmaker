import glob
import os

from rainmaker_app.lib.conf import load
from rainmaker_app.app.profile import Profile
from rainmaker_app.lib import logger

class AppProfiles(object):
    profiles = {}

    def __init__(self,path):
        self.user_dir = path
        self.profiles_dir = os.path.join(path,'profiles')
        self.log=logger.create(self.__class__.__name__)

    def new(self,template=None,vals=None,path=None):
        if template=='unison':
            attrs = load('profile/unison.yml')
        elif not template or template=='base':
            attrs = load('profile/base.yml')
        else:
            self.log.error('Unknown profile type: %s' % template)
            raise AttributeError
        profile = Profile(attrs,vals=vals,path=path)
        profile.user_dir = self.user_dir
        profile.callbacks.register('before_save',self.__auto_profile_path__)
        
        return profile

    def load_paths(self,paths):
        result = []
        for path in paths:
            p = self.load_path(path)
            if p:
                result.append(p)
        return result
    
    def load_path(self,path):
        vals = load(path,abspath=True)
        profile = self.new(vals['type'],vals=vals,path=path)
        return profile

    def find_by(self,key,val,all=False):
        result = []
        for p in self.all():
            if p.attr_val(key) == val:
                if not all:
                    return p
                else:
                    result.append(p)
        if all:
            return result
        return None

    def all(self):
        profiles = []
        for p in glob.glob(os.path.join(self.profiles_dir,'*.yml')):
            profiles.append( self.load_path(p) )
        return profiles

    # Automatically generate filename for new profile
    def __auto_profile_path__(self,**kwargs):
        profile=kwargs['this']
        if profile.path != None:
            return
        profile.path=os.path.join(
            self.profiles_dir,
            "%s.yml" % (profile.title) 
        )
    
