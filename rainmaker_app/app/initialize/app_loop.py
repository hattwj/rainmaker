import os
from time import sleep

from watchdog.observers import Observer
from yaml import safe_dump
from rainmaker_app.lib import logger

class AppLoop(object):
    sync_interval = 5
    observer = None
    log = None
    app = None
    event_log_style= '%(message)s'

    def __init__(self,my_app):
        self.running_profiles = {}
        self.app = my_app
        self.log=logger.create(self.__class__.__name__)
        self.app.callbacks.register('shutdown',self.__shutdown__)
    
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
        
        events_path = os.path.join(self.app.rain_dir,'events', '%s.log' % profile.guid)
        log = logger.create(profile.guid)
        
        handler = profile.handler_init()
        handler.callbacks.register('get_events',self.__log_fs_events__)
        handler.events_log = log 
        logger.send_log_to_file(events_path,log,style=self.event_log_style)
        
        self.running_profiles[profile.guid] = profile
        self.observer.schedule(handler, profile.local_root,recursive=profile.recursive)
        self.log.info('Started profile: %s' % profile.title)
        self.__sync_events__(profile)        
        
    def once(self):
        ''' Process events once '''
        for guid,p in self.running_profiles.iteritems():
            cmds= p.process_events()
            for cmd in cmds:
                out=p.run_cmd(cmd)
                o=p.process_output(out)
    
    def __sync_events__(self,profile):
        ''' sync server side events ''' 
        profile.run_cmd(key='cmd_sync_send')
        profile.run_cmd(key='cmd_sync_recieve')
    
    def __log_fs_events__(self,**kwargs):
        ''' log events for handler '''
        handler=kwargs['this']
        events=kwargs['events']
        for event in events:
            self.log.info('File %s: %s ' % (event['event_type'],event['event_src_path_rel']))
            handler.events_log.info(safe_dump(event))

    def __shutdown__(self,**kwargs):
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

