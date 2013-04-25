import app
import glob
import os

class AppTemplates(object):
    def __init__(self,my_app):
        self.app = my_app
        self.path = self.app.templates_path
        self.templates = self.app.config['templates']
    def find(self,template_type):
        return app.profile.Profile(self.app,data=self.templates[template_type])
        

