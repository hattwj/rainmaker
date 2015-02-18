from .tox_manager import ToxManager
from .fs_manager import FsManager
from .scan_manager import ScanManager
from .sync_manager import SyncManager

class SyncManager(object):
    '''
        Manage a single sync path
    '''
    fs_manager = None
    tox_manager = None
    sync_manager = None
    ready = False

    def __init__(self, sync):
        self.sync = sync
        self.scan_manager = ScanManager(sync)
        self.scan_manager.on_complete = self.scan_complete
        self.scan_manager.start()

    def scan_complete(self, scan_stats):
        print('Scan Completed')
        self.ready = True
        self.sync_manager = SyncManager()
        self.tox_manager = ToxManager(self.sync)
        self.fs_manager = FsManager(self.sync)

        self.tox_manager.on_new_peer = self.on_tox_new_peer
        self.tox_manager.on_fs_event = self.on_tox_fs_event

        self.fs_manager.start()
        self.tox_manager.start()

    def on_tox_new_peer(self, peer):
        print('New peer via tox')
        self.sync_manager.add_peer(sync, peer)

    def on_tox_fs_event(self, fs_event):
        print('Fs Event via tox')

