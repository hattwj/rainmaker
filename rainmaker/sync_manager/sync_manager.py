from .sync_manager import SyncManager

class SyncManager(object):
    '''
        Manage all syncs
    '''
    def __init__(self):
        self.sync_managers = []

    def start(self, sync):
        '''
            Create sync_manager
        '''
        spm = SyncManager(sync)
        spm.on_stop = self.on_sync_manager_stop
        self.sync_managers.append(spm)
        spm.start()
        return spm
    
    def stop(self):
        '''
            Stop all sync path managers 
        '''
        for manager in self.sync_managers:
            manager.stop()

    def on_sync_manager_stop(self, spm):
        '''
            Handle stopped sync path managers
        '''
        print('sync stopped')
        self.sync_managers.remove(spm)


