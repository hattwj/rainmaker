
from rainmaker_app.tox.tox_ring import PrimaryBot, SyncBot
from rainmaker_app.db import models

class ToxManager(object):
    '''
        Manage tox network communications
    '''
    def __init__(self, sync_path):
        self.__active_bot__ = None
        self.peers = []
        self.sync_path = sync_path
        self.primary_bot = PrimaryBot(sync_path.primary_bot_data)
        primary_addr = self.primary_bot.get_address()
        self.sync_bot = SyncBot(primary_addr, sync_path.sync_bot_data)
        
    def start(self):
        '''
            Kick off manager
        '''
        # stub in event handlers
        self.sync_bot.on_start_primary = self.__on_start_primary__
        self.primary_bot.on_peer_connected = self.__on_peer__
        self.sync_bot.on_peer_connected = self.__on_peer__
        self.primary_bot.on_peer_lost = self.__on_peer_lost__
        self.sync_bot.on_peer_lost = self.__on_peer_lost__
        self.primary_bot.on_fs_event = self.__on_fs_event__
        self.sync_bot.on_fs_event = self.__on_fs_event__

        # start searching for primary node
        self.__active_bot__ = self.sync_bot
        self.sync_bot.start()

    def __on_start_primary__(self):
        '''
            sync_bot failed to find primary tox node
        '''
        self.__active_bot__ = self.primary_bot
        self.sync_bot.stop()
        self.primary_bot.start()
    
    @defer.inlineCallbacks
    def __on_peer__(self, tox_pubkey, params):
        '''
            Raise on_new_peer event
        '''
        host = yield Host.find(tox_pubkey=tox_pubkey)
        if host:
            yield host.update_attributes(**params)
        else:
            host = Host(**params)
        yield host.save()
        host.isValid().addCallbackself.on_peer)

    def on_peer(self, peer):
        '''
            Overridden in sync_path manager
        '''
        pass
    
    def __on_peer_lost__(self, peer):
        '''
            remove peer from list
        '''
        self.peers.remove(peer)
    
    @defer.inlineCallbacks
    def __fs_event__(self, friendId, params):
        file_id = params['file_id']
        host_sync = self.friend_to_host_sync(friendId)
        host_file = yield models.HostFile.find(file_id=file_id,
                host_sync_path_id = host_sync_path_id)
        if not host_file:
            host_file =  model.HostFile(**params)
        host_file.save()
        host_file.isValid().addCallback(self.on_fs_event)

    def on_fs_event(self, fs_event):
        '''
            Overridden in sync_path manager
        '''
        pass
    
    def send_fs_event(self, event):
        '''
            broadcast fs_event to chatroom
        '''
        self.__active_bot__.send_fs_event(event)

    def stop(self):
        '''
            Shut down manager
        '''
        self.__active_bot__.stop()
        del(self.peers)
        self.peers = []
        self.stop_sequence_completed()
    
    def on_stop_completed(self):
        '''
            Stop sequence completed
            Overridden in sync_path manager
        '''
        pass
    
    def friend_to_host_sync(self, friendId):
        tox_pubkey = self.__active_bot__.get_client_id(friendId)
        yield HostSync.findOrCreate(
            tox_pubkey=tox_pubkey,
            sync_path_id= self.sync_path.id)
