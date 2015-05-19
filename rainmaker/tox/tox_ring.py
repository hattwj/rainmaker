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
from rainmaker.net.sessions import ToxSessions, tox_auth_strategy 
from rainmaker.net.state import StateMachine, RunLevel
from rainmaker.net.events import EventHandler, EventError
from rainmaker.net.msg_buffer import MsgBuffer


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
    _bootstrap = None
    _sync = None
    sessions = None
    base_group_id = None

    def __init__(self, sync, data=None, primary=None):
        super(ToxBase, self).__init__()
        if data:
            self.load(data)
        self.sync = sync
        self._primary = primary
        self.router = EventHandler(self, auth_strategy=tox_auth_strategy)
        self.events = EventHandler(self)
        self.state_machine = StateMachine()
        self.msg_buffer = MsgBuffer()
        self.register = self.router.register
        self.trigger = self.router.trigger

    def start(self):
        self.state_machine.start()

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

    @primary.setter
    def primary(self, val):
        self._primary = val


class ToxBot(Tox, ToxBase):
    
    def __init__(self, sync=None, data=None, primary=None):
        Tox.__init__(self)
        ToxBase.__init__(self, sync, data=data, primary=primary)
        self.sessions = ToxSessions(self)

def acts_as_connect_bot(tox):
    '''
        Manage tox connection state
    '''
 
    def bootstrap():
        if not tox._bootstrap: 
            tox._bootstrap = tox_env.random_server()
        return tox._bootstrap

    def state_level_changed(name, code, prev_code):
        print('%s: %s %s' % (tox.__class__.__name__, StateMachine.ACTION_NAMES[code], name)) 
        ename = '%s_%s' % (name, StateMachine.ACTION_NAMES[code])
        tox.events.trigger(ename)

    def __conn_run_level__():
        '''
            Base Tox run_level
            - threaded to constantly check tox.do
            - check for shut down
        '''
        def _tox_do():
            do = tox.tox.do
            while True:
                do()
                sleep(0.04)
                if not run_level.should_run:
                    break
        
        def _start():
            ip, port, pubk = tox.bootstrap 
            tox.bootstrap_from_address(ip, port, pubk)
        
        def _stop():
            tox._bootstrap = None
        
        def _valid():
            return tox.isconnected()
        
        _tox_thread = Thread(target=_tox_do)
        _tox_thread.daemon = True
        _tox_thread.start()
        
        name = 'tox_connection'
        run_level = RunLevel(name, _start, _stop, _valid, 30)
        return run_level

    # connection state manager
    tox.state_machine.add(tox.__conn_run_level__())
    tox.state_machine.level_changed = tox.state_level_changed

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
     
    def send(cmd, data=None, fid=None, \
            gid=None, status=None, reply=None):
        '''
            Broadcast event
        '''
        rcode = router.temp(reply, 30) if reply else 0
        for msg in send_buffer(rcode, cmd, status, data):
            if fid is None:
                gid = tox.base_group_id if gid is None else gid
                tox.group_message_send(gid, msg) 
            else:
                tox.send_message(fid, msg)
    
    def on_friend_request(pk, msg):
        '''
            Pass to authenticate
        '''
        for rcode, cmd, status, params in recv_buffer(msg, rcode=pk):
            params['pk'] = pk
            session = tox.sessions.new(pk)
            tox.trigger('authenticate', params=params, session=session)

    def on_friend_message(fid, msg):
        '''
            A friend has sent a message
        '''
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

def acts_as_search_bot(tox, primary):
    tox.primary = primary
    paddr = primary.get_address()

    def __search_run_level__():  
        # ran when level starts
        def _start():
            '''Start tox search'''
            #self.__search_tries_left -= 1
            if len(tox.get_friendlist()) == 0:
                tox.add_friend(paddr, auth_msg)
        
        # ran when level stops
        def _stop():
            #if self.__search_tries_left <= 0:
            #    self.state_machine.stop()
            pass

        # Periodic check to see if level is valid
        def _valid():
            if tox.get_friend_connection_status(0):
                #self.__search_tries_left = 2
                return True
            else:
                try:
                    # try to reach friends
                    for fid in tox.get_friendlist():
                        tox.fsend(fid, 'ping')
                except OperationFailedError as e:
                    pass
                return False
        
        return RunLevel('tox_search', _start, _stop, _valid, 40)

    def on_group_invite(friend_num, gtype, grp_pubkey):
        print('Joining group: %s' % gtype)
        group_id = tox.join_groupchat(friend_num, grp_pubkey)
    
    assert tox.primary is None
    tox.primary = False
    tox.state_machine.add(__search_run_level__())
    tox.on_group_invite = on_group_invite

def acts_as_primary_bot(tox):
    '''
        Primary tox node:
        - create group chat
        - hand off on shutdown
        - Inherited base functions
    '''
    assert tox.primary is None
    tox.primary = True
    # group chat room
    tox.base_group_id = tox.add_groupchat()

def PrimaryBot(app, sync):
    pass

def SyncBot(app, sync):
    pass

