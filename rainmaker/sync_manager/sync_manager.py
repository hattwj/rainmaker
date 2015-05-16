from rainmaker.sync_manager import SyncManager

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

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


'''
    
    When to sync with peers: db.observers
        - On host update event:
            - After auth
            - After recv fs_event
            - Host must set *sync ready* flag
            - mark host as resolving
            - trigger action
    Sync process: sync_manager.actions
        - db, host_transport
        - get sync files since
        - get parts since latest clock from host
        - get latest clock on both sides and run resolver
            - mark host files and parts as *needed*
            - needed marker gets wiped on sync_file bump (already happens)
            - resolver should be able to abort
                - local fs event
                - host down
        - get latest clock on both sides, restart if changed
        - trigger file transfer get requests

    Not Clock Based: sync_manager.utils
        - time based on fs event count

    Separate thread:
        - check db for needed parts
        - x threads parts at a time
            - possibly multiple parts from mult files from mult peers
            - broadcast request for parts
        - 


'''
