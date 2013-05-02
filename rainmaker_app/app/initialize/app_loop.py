import os
from time import sleep
from yaml import safe_dump

from watchdog.observers import Observer

from rainmaker_app.lib import logger
from rainmaker_app.app.profile import ProfileManager

class AppLoop(object):
    observer = None
    log = None
    events_dir = None
    remote_events_dir = None
    running_profiles = None

    def __init__(self,events_dir):
        self.events_dir = events_dir
        self.running_profiles = {}
        self.log=logger.create(self.__class__.__name__)
    
    def start(self,profiles):
        for p in profiles:
            self.start_profile(p)

    # run profile
    def start_profile(self,profile):
        self.log.info('Starting profile: %s' % profile.title)
        
        # require guid
        if profile.guid in self.running_profiles:
            raise AttributeError('Profile already running')
        
        # Start observer if its not already started
        if not self.observer:
            self.observer = Observer()
            self.observer.start()
                
        profile_manager = ProfileManager(profile,self.events_dir)

        self.running_profiles[profile.guid] = profile_manager
        self.observer.schedule(profile_manager.fs_monitor, profile.local_root,recursive=profile.recursive)
        self.log.info('Started profile: %s' % profile.title)
        return profile_manager

    def once(self):
        ''' Process events once '''
        for guid,profile_manager in self.running_profiles.iteritems():
            events= profile_manager.get_events()
            cmds = profile_manager.events_to_cmds(events)
            for cmd in cmds:
                output=profile_manager.run_cmd(cmd)
       
    def shutdown(self,**kwargs):
        if not self.observer:
            return
        self.log.info( "Shutting down...")
        self.observer.unschedule_all()
        #self.log.info("Shutting down thread and fork pool")
        #while len(self.running_profiles) > 0:
        #    p = self.running_profiles.pop()
        #    print 88888888888888888
        #    self.log.info('Stopping profile: %s' % p.title)
        #    self.stop_profile(p)
        self.observer.stop()
        self.observer.join()

