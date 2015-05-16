#from rainmaker.tox_manager import ToxManager
#from rainmaker.fs_manager import FsManager
#from rainmaker.scan_manager import ScanManager
#from rainmaker.sync_manager import SyncManager
from rainmaker.sync_manager.scan_manager import scan_sync

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

    @classmethod
    def singleton(klass, sync):
        spm = klass.__spm__.get(sync.id)
        if spm:
            return spm
        spm = klass(sync)
        klass.__spm__[sync.id] = spm
        return spm

    def __init__(self, sync):
        self.sync = sync
        self.scan_manager = ScanManager(sync)
        self.scan_manager.on_complete = self.scan_complete
    
    def start(self):
        self.scan_manager.start()

    def scan_complete(self, scan_stats):
        log.info('Scan Completed')
        self.ready = True
        self.sync_manager = SyncManager()
        self.tox_manager = ToxManager(self.sync)
        self.fs_manager = FsManager(self.sync)

        self.tox_manager.on_new_peer = self.on_tox_new_peer
        self.tox_manager.on_fs_event = self.on_tox_fs_event

        self.fs_manager.start()
        self.tox_manager.start()

    def on_tox_new_peer(self, peer):
        log.info('New peer discovered via tox')
        self.sync_manager.add_peer(sync, peer)

    def on_tox_fs_event(self, fs_event):
        log.info('Fs Event via tox')

