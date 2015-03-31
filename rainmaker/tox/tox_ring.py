# stdlib imports
from __future__ import print_function
from warnings import warn
from threading import Thread
from time import sleep

# lib imports
from pytox import Tox, OperationFailedError

# local imports
from rainmaker.main import Application
from rainmaker.tox import tox_env
from rainmaker.tox import tox_errors

from rainmaker.net.state import StateMachine, RunLevel
from rainmaker.net.events import EventHandler, EventError
from rainmaker.net.msg_buffer import recv_buffer, send_buffer

def require_auth(func):
    '''
        Event responder decorator to require auth
    '''
    def wrapper(self, event):
        friend_id = event.params.get('friend_id', None)
        if friend_id is None:
            raise tox_errors.ToxAuthorizationError()
        if friend_id not in self.__authenticated_friends__:
            raise tox_errors.ToxAuthorizationError()
        func(self, event)
    return wrapper
 
class ToxBase(Tox):

    '''
        Base class with overrides/defaults for Tox
    '''

    running = False
    was_connected = False
    ever_connected = False
    _bootstrap = None

    def __init__(self, data=None):
        self.__authenticated_friends__ = set()
        Tox.__init__(self)
        if data:
            self.load(data)
        # events received from tox client
        self.router = EventHandler(self)
        # events handler
        self.events = EventHandler(self)
        # connection state manager
        self.state_machine = StateMachine()
        self.state_machine.add(self.__conn_run_level__())
        self.start = self.state_machine.start
        self.stop = self.state_machine.stop
        self.state_machine.level_changed = self.state_level_changed
        self.router.register('ping', self.__cmd_ping__)
        self.router.register('pong', self.__cmd_pong__)
    
    @property
    def bootstrap(self):
        if not self._bootstrap: 
            self._bootstrap = tox_env.random_server()
        return self._bootstrap

    def state_level_changed(self, name, code, prev_code):
        print('%s: %s %s' % (self.__class__.__name__, StateMachine.ACTION_NAMES[code], name)) 
        ename = '%s_%s' % (name, StateMachine.ACTION_NAMES[code])
        self.events.call_event(ename)

    def __conn_run_level__(self):
        '''
            Base Tox run_level
            - threaded to constantly check tox.do
            - check for shut down
        '''
        def _tox_do():
            do = self.do
            while True:
                do()
                sleep(0.04)
                if not run_level.should_run:
                    break
        
        def _start():
            ip, port, pubk = self.bootstrap 
            self.bootstrap_from_address(ip, port, pubk)
        
        def _stop():
            self._bootstrap = None
        
        def _valid():
            return self.isconnected()
        
        _tox_thread = Thread(target=_tox_do)
        _tox_thread.daemon = True
        _tox_thread.start()
        
        name = 'tox_connection'
        run_level = RunLevel(name, _start, _stop, _valid, 30)
        return run_level
    
    def on_read_reciept(self, fno, reciept):
        print('friend: %s recv: %s' % (fno, reciept))

    def on_dht_connected(self):
        print('dht-connnected-event')

    def on_dht_disconnected(self):
        print('dht-disconnected-event')

    def on_friend_request(self, pk, msg):
        '''
            Pass to authenticate
        '''
        key = 'tox-fr-%s-%s' % (id(self), pk)
        for cmd, params in recv_buffer(key, msg):
            params = {
                'friend_pk': pk,
                'params': params
            }
            self.router.call_event('authenticate', params=params)

    def on_friend_message(self, fid, msg):
        '''
            A friend has sent a message
        '''
        # manage reply from handler
        def freply(event):
            self.fsend(fid, event.name, event.val())
        
        # Generate a unique key for this request
        key = 'tox-fm-%s-%s' % (id(self), fid)
        # Only yield when msg is complete
        for cmd, params in recv_buffer(key, msg):
            params = {
                'friend_id': fid,
                'params': params
            }
            self.router.call_event(cmd, params=params, reply=freply)

    def on_group_message(self, gno, fid, msg):
        '''
            A group member sent a message
        '''
        def greply(event):
            self.gsend(event.name, event.val())

        key = 'tox-gm-%s-%s-%s' % (id(self), gno, fid)
        for cmd, params in recv_buffer(key, msg):
            params = {
                'friend_id': fid,
                'group_number': gno,
                'params': params
            }
            self.router.call_event(cmd, params=params, reply=greply)

    def gsend(self, cmd, data=None):
        '''
            Broadcast event
        '''
        for count, msg in send_buffer(cmd, data, chunk=1300):
            self.group_message_send(self.base_group_id, msg) 

    def fsend(self, fid, cmd, data=None):
        '''

        '''
        for count, msg in send_buffer(cmd, data, chunk=1300):
            self.send_message(fid, msg)

    def __cmd_pong__(self, event):
        pass

    def __cmd_ping__(self, event):
        event.reply('pong')

class SyncBot(ToxBase):
    '''
        Find primary bot and relay information or bail
        if timeout reached
    '''
    def __init__(self, primary_bot, data=None):
        ToxBase.__init__(self, data)
        self.primary = False
        self.primary_bot = primary_bot
        self.state_machine.add(self.__search_run_level__())
        self.__host = Event('put_host', pubkey=self.get_address(), 
            device_name=Application.device_name,
            version=Application.version).serialize()
        
    def __search_run_level__(self): 
        
        # ran when level starts
        def _start():
            '''Start tox search'''
            #self.__search_tries_left -= 1
            if len(self.get_friendlist()) == 0:
                self.add_friend(self.primary_bot.get_address(), auth_msg)
        
        # ran when level stops
        def _stop():
            #if self.__search_tries_left <= 0:
            #    self.state_machine.stop()
            pass

        # Periodic check to see if level is valid
        def _valid():
            if self.get_friend_connection_status(0):
                #self.__search_tries_left = 2
                return True
            else:
                try:
                    # try to reach friends
                    for fid in self.get_friendlist():
                        self.fsend(fid, 'ping')
                except OperationFailedError as e:
                    pass
                return False
        
        return RunLevel('tox_search', _start, _stop, _valid, 40)

    def on_group_invite(self, friend_num, gtype, grp_pubkey):
        print('Joining group: %s' % gtype)
        group_id = self.join_groupchat(friend_num, grp_pubkey)
             
class PrimaryBot(ToxBase):
    '''
        Primary tox node:
        - create group chat
        - hand off on shutdown
        - Inherited base functions
    '''
    
    def __init__(self, data=None):
        self.primary = True
        super(PrimaryBot, self).__init__(data)
        self.sync_bot = None

        # event handlers 
        self.router.register('join_chat', self.__cmd_join_chat__)
        
        # group chat room
        self.base_group_id = self.add_groupchat()
 
    def stop(self):
        super(PrimaryBot, self).stop()
    
    def start(self):
        assert self.sync_bot is not None
        if self.state_machine.running:
            print('Already running')
            return
        super(PrimaryBot, self).start()
     
    @require_auth
    def __cmd_join_chat__(self, event):
        '''
            Someone requested access to chat room
            - TODO: Verify that they haven't already joined
        '''
        fid = event.val('friend_id')
        self.invite_friend(fid, self.base_group_id)
    
