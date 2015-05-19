from rainmaker.sync_manager.fs_manager import SyncWatch
import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

from warnings import warn
from queue import Queue

from rainmaker.net.controllers import register_controller_routes
from rainmaker.tox.tox_ring import PrimaryBot, SyncBot
from rainmaker.db.main import Sync

class FsManager(object):
    def __init__(self, app, sync):
        self.app = app
        self.sync = sync

    def start(self):
        self.watcher = SyncWatch(self.app, self.sync)

class ToxManager(object):
    '''
        Manage tox network communications
        - A tox interface for sync_manager
        - Stores data on close
        - starts tox
        - switches to primary if primary missing
    '''
    def __init__(self, app, sync):
        # assign vars
        self.sync = sync
        self.stopping = False
        
        # create bots
        self.primary_bot = PrimaryBot(sync, data=sync.tox_primary_blob)
        self.sync_bot = SyncBot(sync, primary=self.primary_bot, data=sync.tox_sync_blob)
        register_controller_routes(app.db, self.primary_bot)
        register_controller_routes(app.db, self.sync_bot)

        self.sync_bot.on_stop = self.__on_stop__

    def start(self):
        '''
            Kick off manager
        '''
        self.stopping = False 
        # start searching for primary node
        self.sync_bot.start()
          
    def stop(self):
        '''
            Shut down manager
        '''
        self.stopping = True
        self.sync_bot.stop()
    
    def __on_stop__(self, *args):
        if not self.stopping:
            warn('Premature tox exit')
        # Store tox data
        self.sync.tox_primary_blob = self.primary_bot.save()
        self.sync.tox_sync_blob = self.sync_bot.save()
        self.on_stop()

    def on_stop(self):
        '''
            Stop sequence completed
            Overridden in sync manager
        '''
        pass 

from rainmaker.sync_manager.scan_manager import scan_sync, refresh_sync
class SyncPathManager(object):
    '''
        Manage a single sync path
    '''

    def __init__(self, app, sync):
        self.app = app
        self.sync = sync
        self.fs_manager = FsManager(app, sync)
        self.tox_manager = ToxManager(app, sync)
    
    def start(self): 
        log.info('Starting scan of: %s' % self.sync.path)
        scan_sync(self.sync)
        log.info('Scan completed of: %s' % self.sync.path)
        log.info(scan_stats)
        self.ready = True
        self.fs_manager.start()
        self.tox_manager.start()

class SyncManager(object):
    '''
        Manage all syncs
    '''
    def __init__(self, app):
        self.syncs = {}
        self.app = app
    
    def start(self):
        syncs = self.app.db.query(Sync).all()
        for sync in syncs:
            spm = self.add_sync(sync)
        
    def add_sync(self, sync):
        spm = SyncPathManager(self.app, sync)
        spm.setup()
        self.syncs[sync.id] = spm
        return spm
        
    def host_sync(self, host):
        self.app.db.submit(sync_with_host, self.app.db, host.sync, host)

