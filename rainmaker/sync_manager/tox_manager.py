from warnings import warn
from queue import Queue

from rainmaker_app.tox.tox_ring import PrimaryBot, SyncBot
from rainmaker_app.db import models

class ToxRunner(object):
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
        self.primary_bot = PrimaryBot(sync, data=sync.tox_primary_blob)
        self.sync_bot = SyncBot(sync, primary=self.primary_bot, data=sync.tox_sync_blob)
        self.sync_bot.on_stop = self.__on_stop__
        self.register = self.sync_bot.register

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

    def commit(self):
        self.sync_bot.commit()

