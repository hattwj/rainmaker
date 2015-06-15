# stdlib imports
from __future__ import print_function
#from abc import ABCMeta, abstractmethod
from warnings import warn
from threading import Thread
from time import sleep

# lib imports
from pytox import Tox, OperationFailedError

# local imports
from rainmaker.tox import tox_env
from rainmaker.tox import tox_errors
from rainmaker.net.controllers import register_controller_routes
from rainmaker.net.sessions import ToxSessions, tox_auth_strategy 
from rainmaker.net.state import StateMachine, RunLevel
from rainmaker.net.events import EventHandler, EventError
from rainmaker.net.msg_buffer import MsgBuffer

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)


'''
    - Ring func, pass in sync
    - Dont subclass Tox, proxy it instead
    - Proxy receives tox, mock tox param for testing 
'''
class ToxBase(object):
    '''
        Base class with overrides/defaults for Tox
        - mixin class
    '''
    running = False
    was_connected = False
    ever_connected = False
    sessions = None
    base_group_id = None

    def __init__(self, sync, data=None, primary=None, tox_manager=None):
        super(ToxBase, self).__init__()
        if data:
            self.load(data)
        self.sync_id = sync.id
        self.primary = primary
        self.tox_manager = tox_manager
        self.router = EventHandler(self, auth_strategy=tox_auth_strategy)
        self.actions = EventHandler(self)
        self.state_machine = StateMachine()
        self.msg_buffer = MsgBuffer()
        self.register = self.router.register
        self.trigger = self.router.trigger

    def start(self):
        return self.state_machine.start()

    def stop(self):
        self.state_machine.stop()
 
    def send(self, cmd, data=None, fid=None, status=None, reply=None):
        raise NotImplementedError()

    def group_message_send(self, gid, data):
        raise NotImplementedError()

    def send_message(self, fid, msg):
        raise NotImplementedError()
     
    @property
    def primary(self):
        return self._primary if self._primary else self
    
    @property
    def is_primary(self):
        return self.primary == self

    @primary.setter
    def primary(self, val):
        self._primary = val


class ToxBot(Tox, ToxBase):
    
    def __init__(self, *args, **kwargs):
        Tox.__init__(self)
        ToxBase.__init__(self, *args, **kwargs)
        self.sessions = ToxSessions(self)

def acts_as_connect_bot(tox):
    '''
        Manage tox connection state
    '''
     
    def state_level_changed(name, code, prev_code):
        log.info('%s: %s %s' % (tox.__class__.__name__, StateMachine.ACTION_NAMES[code], name)) 
        ename = '%s_%s' % (name, StateMachine.ACTION_NAMES[code])
        tox.actions.trigger(ename)

    def __conn_run_level__():
        '''
            Base Tox run_level
            - threaded to constantly check tox.do
            - check for shut down
        '''
        
        def _start():
            msg = 'PrimaryBot' if tox.is_primary else 'SyncBot'
            log.info('%s starting' % msg)
            ip, port, pubk = tox_env.random_server()
            tox.bootstrap_from_address(ip, port, pubk)
            if not tox.is_primary and _start.first_run:
                tox.actions.trigger('add_primary')
                _start.first_run = False
        _start.first_run = True

        def _stop():
            msg = 'PrimaryBot' if tox.is_primary else 'SyncBot'
            log.info('%s stopping' % msg)
        
        def _valid():
            return tox.isconnected()
         
        name = 'tox_connection'
        run_level = RunLevel(name, _start, _stop, _valid, 30)
         
        def _tox_do():
            do = tox.do
            while True:
                do()
                sleep(0.04)
                if not run_level.should_run:
                    break
        log.info('ConnectBot thread')
        _tox_thread = Thread(target=_tox_do)
        _tox_thread.daemon = True
        _tox_thread.start()
        
        return run_level

    # connection state manager
    tox.state_machine.add(__conn_run_level__())
    tox.state_machine.level_changed = state_level_changed

def acts_as_message_bot(tox):
    '''
        compose Bots to manage individual tasks
        - connection
        - text
        - file transfer
    ''' 
    router = tox.router
    send_buffer = tox.msg_buffer.send
    recv_buffer = tox.msg_buffer.recv
     
    def send(cmd, data=None, fid=None, addr=None, \
            gid=None, status=None, reply=None):
        '''
            Broadcast event
        '''
        assert (fid is not None) or (gid is not None) or (addr is not None)
        
        if addr:
            assert fid is None
            assert gid is None
            fid = tox.get_friend_id(addr)
            if fid is None:
                print('NEW FID: ', tox.add_friend_norequest(addr))
                fid = tox.get_friend_id(addr)
                assert fid is not None
        # wait 30 seconds max for reply
        rcode = router.temp(reply, 30) if reply else 0
        # send message
        for msg in send_buffer(rcode, cmd, status, data):
            if gid:
                tox.group_message_send(gid, msg) 
            else:
                tox.send_message(fid, msg)

    def on_friend_request(pk, msg):
        '''
            Pass to authenticate
        '''
        print('Friend Request')
        
        #for rcode, cmd, status, params in recv_buffer(msg, rcode=pk):
        #    params['pk'] = pk
        #    session = tox.sessions.new(pk)
        #    tox.trigger('authenticate', params=params, session=session)

    def on_friend_message(fid, msg):
        '''
            A friend has sent a message
        '''
        print('friend message')
        on_message(None, fid, msg)

    def on_message(gid, fid, msg):
        '''
            A group member sent a message
        '''
        def do_reply(event):
            tox.send(rcode, event.val(), status=event.status, gid=gid, fid=fid)
        rcode = -1
        for rcode, cmd, status, params in recv_buffer(msg):
            params['fid'] = fid
            params['gid'] = gid
            session = tox.sessions
            _reply = do_reply if rcode else None            
            tox.trigger(cmd, params=params, reply=_reply, \
                    rcode=rcode, status=status, session=session)

    # events received from tox client
    tox.on_group_message = on_message
    tox.on_friend_message = on_friend_message
    tox.on_friend_request = on_friend_request
    tox.send = send

def acts_as_search_bot(tox):
    primary = tox.primary

    def __search_run_level__():  
        # ran when level starts
        def _start():
            '''
                Start tox search
                - send a request to friend primary
            '''
            log.info('SearchBot starting...')
            #self.__search_tries_left -= 1
            if len(tox.get_friendlist()) == 0:
                tox.actions.trigger('add_primary')

        # ran when level stops
        def _stop():
            log.info('SearchBot stopping...')
            #if self.__search_tries_left <= 0:
            #    self.state_machine.stop()
            pass

        # Periodic check to see if level is valid
        def _valid():
            fid = tox.get_friend_id(tox.primary.get_address())
            if tox.get_friend_connection_status(fid):
                #self.__search_tries_left = 2
                return True
            else:
                try:
                    # try to reach friends
                    pass
                    for fid in tox.get_friendlist():
                        print('search validation')
                        addr = tox.get_client_id(fid)
                        tox.actions.trigger('ping', {'addr':  addr})
                except OperationFailedError as e:
                    pass
                return False
        
        return RunLevel('tox_search', _start, _stop, _valid, 40, rate=5)

    def on_group_invite(friend_num, gtype, grp_pubkey):
        log.info('Joining group: %s' % gtype)
        group_id = tox.join_groupchat(friend_num, grp_pubkey)
    
    tox.state_machine.add(__search_run_level__())
    tox.on_group_invite = on_group_invite

def acts_as_primary_bot(tox):
    '''
        Primary tox node:
        - create group chat
        - hand off on shutdown
        - Inherited base functions
    '''
    tox.primary = tox
    # group chat room
    tox.base_group_id = tox.add_groupchat()
    
'''
    Alias ToxBot to allow debug / testing
'''
DefaultBot = ToxBot

def PrimaryBot(DbConn, sync, **kwargs):
    '''
        Primary Bot
    '''
    tox = DefaultBot(sync, **kwargs)
    acts_as_connect_bot(tox)
    acts_as_message_bot(tox)
    acts_as_primary_bot(tox)
    register_controller_routes(DbConn, tox)
    return tox

def SyncBot(DbConn, sync, **kwargs):
    tox = DefaultBot(sync, **kwargs)
    acts_as_connect_bot(tox)
    acts_as_message_bot(tox)
    acts_as_search_bot(tox)
    register_controller_routes(DbConn, tox)
    return tox
