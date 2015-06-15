from rainmaker.sync_manager.fs_manager import SyncWatch
import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

from warnings import warn
from queue import Queue

from rainmaker.net.controllers import register_controller_routes
from rainmaker.tox.tox_ring import PrimaryBot, SyncBot
from rainmaker.db.main import Sync

class FsManager(object):
    def __init__(self, spm):
        self.sync_path_manager = spm
        self.app = spm.sync_manager.app
        self.sync = spm.sync

    def start(self):
        self.watcher = SyncWatch(self.app.db, self.sync)

class ToxManager(object):
    '''
        Manage tox network communications
        - A tox interface for sync_manager
        - Stores data on close
        - starts tox
        - switches to primary if primary missing
    '''

    def __init__(self, spm):
        self.sync_path_manager = spm
        self.app = spm.app
        # assign vars
        sync = spm.sync
        self.sync = sync
        self.stopping = False
        
        # create bots
        self.primary_bot = PrimaryBot(sync,
                tox_manager=self,
                data=sync.tox_primary_blob)
        self.sync_bot = SyncBot(sync, 
                tox_manager=self,
                primary=self.primary_bot, data=sync.tox_sync_blob)
        register_controller_routes(self.app.db, self.primary_bot)
        register_controller_routes(self.app.db, self.sync_bot)

        self.sync_bot.on_stop = self.__on_stop__

    def start(self, start_primary=False):
        '''
            Kick off manager
        '''
        
        log.info('ToxManager: start! %s' % self.sync.path )
        self.stopping = False 
        if start_primary:
            print('Primary'*30)
            self.primary_bot.start()
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

    def add_friend(self, tox, addr):
        '''
        '''
        ptox = self.primary_bot

        def _do_auth(event):
            nonce = event.val('nonce')
            passwd_hash = ptox.sessions.get_hash(addr, nonce)
            params = {'pk': ptox.get_address(), 'passwd_hash': passwd_hash}
            tox.trigger('create_session', 
                    params=params, reply=_check_auth)  
            _do_auth.ran = True

        def _check_auth(event):
            assert event.status == 'ok'
            _check_auth.ran = True
        
        args = {'pk': addr}
        tox.trigger('new_session', params=args, reply=_do_auth)

    def ping(self, tox, addr):
        log.info('Pinging...')
        params = {'pk': addr}
        tox.trigger('ping', params=params)

from rainmaker.sync_manager.scan_manager import scan_sync, refresh_sync
class SyncPathManager(object):
    '''
        Manage a single sync path
    '''

    def __init__(self, manager, sync):
        self.sync_manager = manager
        self.app = manager.app
        self.sync = sync
        self.fs_manager = FsManager(self)
        self.tox_manager = ToxManager(self)
    
    def start(self, start_primary=False): 
        self.scan()
        self.fs_manager.start()
        self.tox_manager.start(start_primary)

    def scan(self):
        log.info('%s starting scan of %s' % (self.app.device_name, self.sync.path))
        stats = scan_sync(self.app.db, self.sync)
        log.info('Scan completed of: %s' % self.sync.path)
        log.info(stats)

class SyncManager(object):
    '''
        Manage all syncs
    '''
    def __init__(self, app):
        self.syncs = []
        self.app = app
        
    def add_sync(self, sync):
        spm = SyncPathManager(self, sync)
        self.syncs.append(spm)
        return spm
       
    def sync_with_host(self, host):
        db = self.app.Session()
        sync_with_host(db, host.sync, host)

