import glob
import os


from rainmaker_app.conf import load
from rainmaker_app.app.model import BaseProfile
from rainmaker_app.lib import logger

class AppProfiles(object):
    profiles = {}

    def __init__(self,my_app):
        self.app=my_app
        self.log=logger.create(self.__class__.__name__)

    def new(self,template=None,vals=None,path=None):
        if template=='unison':
            attrs = load('model/unison_profile/attrs.yml')
        elif not template or template=='base':
            attrs = load('model/base_profile/attrs.yml')
        else:
            self.log.error('Unknown profile type: %s' % template)
            raise AttributeError
        profile = BaseProfile(attrs,vals=vals,path=path)
        profile.callbacks.register('before_save',self.__auto_profile_path__)
        
        return profile

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
        for p in glob.glob(self.app.profiles_dir('*.yml')):
            profiles.append( self.load_path(p) )
        return profiles

    # Automatically generate filename for new profile
    def __auto_profile_path__(self,**kwargs):
        profile=kwargs['this']
        if profile.path != None:
            return
        profile.path=os.path.join(
            self.app.rain_dir,
            'profiles',
            "%s.yml" % (profile.title) 
        )
    
