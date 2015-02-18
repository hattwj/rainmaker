from twisted.internet import defer
from rainmaker_app.tox.tox_ring import PrimaryBot, SyncBot
from rainmaker_app.db import models

class ToxManager(object):
    '''
        Manage tox network communications
        - A tox interface for sync_manager
        - Stores data on close
        - starts tox
        - switches to primary if primary missing
    '''
    def __init__(self, sync):
        # assign vars
        self.__active_bot__ = None
        self.sync = sync
        self.stopping = False
        # create bots
        self.primary_bot = PrimaryBot(sync.tox_primary_bot_data)
        primary_addr = self.primary_bot.get_address()
        self.sync_bot = SyncBot(primary_addr, sync.tox_sync_bot_data)
    
    def store_data(self):
        '''
            Store tox data
        '''
        self.sync.tox_primary_bot_data = self.primary_bot.save()
        self.sync.tox_sync_bot_data = self.sync_bot.save()

    def start(self):
        '''
            Kick off manager
        '''
        self.stopping = False
        def _on_primary(*args):
            '''
                sync_bot failed to find primary tox node
            '''
            self.__active_bot__ = self.primary_bot
            if not self.stopping:
                d = self.primary_bot.start()
        
        def _on_exit(*args):
            if not self.stopping:
                print('Premature tox exit')
            self.store_data()
            self.on_stop()
                
        # start searching for primary node
        self.__active_bot__ = self.sync_bot
        d = self.sync_bot.start()
        d.addCallback(_on_primary)
        d.addCallback(_on_exit)
        return d
        
    @defer.inlineCallbacks
    def __on_peer__(self, tox_pubkey, params):
        '''
            process on_new_peer event
        '''
        host = yield Host.find(tox_pubkey=tox_pubkey)
        if host:
            yield host.update_attributes(**params)
        else:
            host = Host(**params)
        host.save().addCallback(self.on_peer)
 
    @defer.inlineCallbacks
    def __fs_event__(self, friendId, params):
        '''
            Incoming fs event handler
        '''
        file_id = params['file_id']
        host_sync = self.friend_to_host_sync(friendId)
        host_file = yield models.HostFile.find(file_id=file_id,
                host_sync_id = host_sync_id)
        if not host_file:
            host_file =  model.HostFile(**params)
        host_file.save()
        host_file.isValid().addCallback(self.on_fs_event)
 
    def send_fs_event(self, event):
        '''
            broadcast fs_event to chatroom
        '''
        self.__active_bot__.send_fs_event(event)

    def stop(self):
        '''
            Shut down manager
        '''
        self.stopping = True
        self.__active_bot__.stop()
    
    def on_stop(self):
        '''
            Stop sequence completed
            Overridden in sync manager
        '''
        pass    
