#from rainmaker.tox_manager import ToxManager
#from rainmaker.fs_manager import FsManager
#from rainmaker.scan_manager import ScanManager
#from rainmaker.sync_manager import SyncManager
from rainmaker.sync_manager.scan_manager import scan_sync, refresh_sync

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

class SyncPathManager(object):
    '''
        Manage a single sync path
    '''
    fs_manager = None
    tox_manager = None
    sync_manager = None
    ready = False

    __spm__ = {}

    def __init__(self, app, sync):
        self.app = app
        self.sync = sync
        self.fs_manager = FsManager(app, sync)
        self.tox_manager = ToxManager(app, sync)
        self.tox_manager.on_new_peer = self.on_tox_new_peer
        self.tox_manager.on_fs_event = self.on_tox_fs_event
    
    def start(self): 
        log.info('Starting scan of: %s' % self.sync.path)
        scan_sync(self.sync)
        log.info('Scan completed of: %s' % self.sync.path)
        log.info(scan_stats)
        self.ready = True
        self.fs_manager.start()
        self.tox_manager.start()

