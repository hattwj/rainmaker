from .sync_path_manager import SyncPathManager

class SyncManager(object):
    '''
        Manage all sync_paths
    '''
    def __init__(self):
        self.sync_path_managers = []

    def start(self, sync_path):
        '''
            Create sync_path_manager
        '''
        spm = SyncPathManager(sync_path)
        spm.on_stop = self.on_sync_path_manager_stop
        self.sync_path_managers.append(spm)
        spm.start()
        return spm
    
    def stop(self):
        '''
            Stop all sync path managers 
        '''
        for manager in self.sync_path_managers:
            manager.stop()

    def on_sync_path_manager_stop(self, spm):
        '''
            Handle stopped sync path managers
        '''
        print('sync stopped')
        self.sync_path_managers.remove(spm)

