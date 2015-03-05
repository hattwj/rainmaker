from warnings import warn
from queue import Queue

from rainmaker_app.tox.tox_ring import PrimaryBot, SyncBot
from rainmaker_app.db import models

'''
    Send and recv file status
    - mark files as:
        - needed
        - out of date
        - current
        - conflict
    - 
'''

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
        self.primary_bot = PrimaryBot(sync.tox_primary_blob)
        self.sync_bot = SyncBot(self.primary_bot, sync.tox_sync_blob)
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

def HostsController(session, sync, tr):
    '''
        put
    '''
    def _cmd_put_host(event):
        ''' Handle put host command '''
        p = event.get('host').require('pubkey', 'device_name').val()
        pubkey = p['pubkey']
        device_name = p['device_name']
        host = session.query(Host).filter(
                Host.sync_id == sync.id,
                Host.pubkey == pubkey).first()
        if not host:
            host = Host(sync_id=sync.id, pubkey=pubkey)
        host.device_name = device_name
        session.add(host)
        session.commit()

    def _cmd_list_host(event):
        hosts = session.query(Host).filter(
                Host.sync_id == sync.id
            ).all()
        for h in hosts:
            event.reply('put_host', host=h.to_dict())

    tr.register('put_host', _cmd_put_host)
    tr.register('list_host', _cmd_list_host)
    return tr

def HostFilesController(session, sync, host, tr):
    '''
        session: Database session
        sync: sync path
        tr: transport
    '''

    def _cmd_put_host_file(event):
        ''' Handle put file command '''
        p = event.get('host_file')
        p.require('rel_path', 'id', 'is_dir', 'does_exist')
        p = p.allow('file_hash').val()
        host_file = session.query(HostFile).filter(
            HostFile.host_id == host.id,
            HostFile.id == p['id']).first()
        if not host_file:
            host_file = HostFile()
        host_file.update_attributes(**p)
        session.add(host_file)
        session.commit()

    def _cmd_get_host_file(event):
        ''' Handle get host file command '''
        p = event.val('id')
        host_file = session.query(HostFile).filter(
            HostFile.host_id == host.id,
            HostFile.id == p['id']).first()
        if host_file:
            event.reply('put_host_file', host_file.to_dict())

    tr.register('put_host_file', _cmd_put_host_file)
    tr.register('get_host_file', _cmd_put_host_file)

