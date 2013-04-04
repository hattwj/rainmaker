import app
import glob
import os

class AppProfiles(object):
    profiles = {}

    def __init__(self,my_app):
        self.app=my_app

        self.app.callbacks.add('after_init',self.after_app_init)
        
    def after_app_init(self):
        for p in glob.glob(self.app.profiles_path,'*.yml'):
            profile = app.model.Profile(p)
            self.profiles[p] = profile
    
    def new(self,template='unison'):
        profile=None
        if template=='unison':
            profile = app.model.UnisonProfile(self.app)
        profile.callbacks.register('before_save',self.auto_profile_path)
        return profile

    def load(self,path):
        profile = Profile(my_app,path=path)
        return profile

    def find_by(self,key):
        if key in self.profiles:
            return self.profiles[key]
        else:
            pass
    def all(self):
        pass

    def auto_profile_path(self,**kwargs):
        profile=kwargs['this']
        if profile.path != None:
            return
        profile.path=os.path.join(
            self.app.rain_dir,
            'profiles',
            "%s-%s.yml" % (profile.name,profile.profile_type) 
        )
