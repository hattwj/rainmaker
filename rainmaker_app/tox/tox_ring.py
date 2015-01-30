# stdlib imports
from __future__ import print_function
from warnings import warn
from sys import exit
from time import sleep
from os.path import exists

# lib imports
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from pytox import Tox

# local imports
import tox_env
import tox_errors

import yaml

def parse(line):
    request = yaml.safe_load(line)
    cmd = request.get('command', None)
    params = rquest.get('params', {})
    return [cmd, params]


class Event(object):
    def __init__(self, name, source, args, kwargs):
        self.name = name
        self.source = source
        self.args = args
        self.kwargs = kwargs

class EventHandler(object):

    def __init__(self, parent):
        self.parent = parent
        self.__cmds__ = {}
    
    def call_event(name, *args, **kwargs):
        event = Event(cmd, self.parent, args, kwargs)
        funcs = self.__cmds__.get(name, None)
        if funcs is None:
            self.handler_missing(event)
            return
        for f in funcs:
            if f(event) == False:
                break
    
    def handler_missing(self, event):
        print('no handlers for %s' % event.name)

    def register(self, name, func):
        if name not in self.__cmds__:
            self.__cmds__[name] = []
        self.__cmds__[name].append(func)

class Timer(object):
    '''
        Generic timer that will run after timeout elapsed
    '''
    def __init__(self, timeout, func, loop=False):
        self.timeout = timeout
        self.func = func
        self.loop = loop
        self._timer = None
        self.ran = False

    @property
    def running(self):
        '''
            Is the timer running?
        '''
        return self._timer.active()

    def reset(self):
        '''
            Reset timer, restart if off
        '''
        self.off()
        self.on()
    
    def _run(self):
        '''
            Run the timer
        '''
        self.func()
        self.ran = True
        if self.loop:
            self.on()

    def on(self):
        '''
            Turn the timer on
        '''
        self._timer = reactor.callLater(self.timeout, self._run)

    def off(self):
        '''
            Turn the timer off
        '''
        if self._timer and self._timer.active():
            self._timer.cancel()

class ToxBase(Tox):
    '''
        Base class with overrides/defaults for Tox
    '''

    running = False
    was_connected = False
    ever_connected = False

    def __init__(self, data=None):
        Tox.__init__(self)
        if data:
            self.load(data)
        router = EventHandler(self)
        self.router = router
        self.register = router.register
        self.call_event = router.call_event
        self.handler_missing = router.handler_missing

    def on_friend_request(self, pk, message):
        self.add_friend_norequest(pk)
    
    def start(self):
        if self.running:
            warn('Already running')
            return
        self.running = True
        self.connect_timer = Timer(tox_env.TIMEOUT, self.connect)
        self.connect()
        self._loop = LoopingCall(self.loop)
        d = self._loop.start(0.01)
        d.addErrback(self.__connect_loop_failed__)

    def __connect_loop_failed__(self, reason):
        print('Uncaught error caused tox connection failure')
        print(reason)
        raise ToxConnectionError('uncaught error')

    def connect(self):
        print('connecting...')
        ip, port, pubk = tox_env.random_server()
        self.bootstrap_from_address(ip, port, pubk)
        self.connect_timer.reset()
         
    def loop(self): 
       is_connected = self.isconnected()
       if not self.was_connected and is_connected:
           self.connect_ever = True
           self.connect_timer.off()
           self.on_dht_connected()
       if self.was_connected and not is_connected:
           self.on_dht_disconnected()
           self.connect()
       self.do()
       self.was_connected = is_connected

    def shutdown(self):
        self._loop.stop()
        self.connect_timer.off()
        self.kill()
    
    def on_read_reciept(self, fno, reciept):
        print('friend: %s recv: %s' % (fno, reciept))

    def on_dht_connected(self):
        print('dht-con')

    def on_dht_disconnected(self):
        print('dht-dis')

    def on_friend_message(self, friend_id, message):
        cmd, params = parse(message)
        params['friend_id'] = friend_id
        self.call_event(cmd, **params)

    def on_group_message(self, group_number, friend_id, message):
        cmd, params = parse(message)
        params['friend_id'] = friend_id
        params['group_number'] = group_number
        self.call_event(cmd, **params)

    def send_fs_event(self, event):
        '''
            Broadcast fs_event
        '''
        raise NotImplementedError('wip')
    

class SyncBot(ToxBase):
    '''
        Find primary bot and relay information or bail
        if timeout reached
    '''
    def __init__(self, data):
        ToxBase.__init__(self)
        self.primary = False
        self.abort_timer = Timer(tox_env.TIMEOUT, self.__abort__)
        self.search_timer = Timer(3, self.__search__, loop=True)
        #self.set_name("SyncBot: %s" % tox_env.DATA) 
        
    def on_dht_connected(self):
        self.abort_timer.on()
        self.search_timer.on()

    def on_dht_disconnected(self):
        self.abort_timer.off()
        self.search_timer.off()
    
    def on_group_invite(self, friend_num, gtype, grp_pubkey):
        print('Joining group %s' % gtype)
        group_id = self.join_groupchat(friend_num, grp_pubkey)
        
    def __search__(self):
        '''
            Try to find primary
        '''
        if len(self.get_friendlist()) == 0:
            print('Adding primary')
            self.add_friend(primary.get_address(), tox_env.PASSWORD)
        if self.get_friend_connection_status(0):
            print('Primary found!')
            self.abort_timer.off()
        else:
            if not self.abort_timer.running:
                self.abort_timer.on()
            print('Primary not found')

    def __abort__(self):
        '''
            Stop searching and start primary
        '''
        self.search_timer.off()
        self.disconnect()
        self.on_start_primary()
    
    def on_start_primary(self, event):
        '''
            Overridden in tox_manager
        '''
        raise NotImplementedError('Override this method')
 
class PrimaryBot(ToxBase):
    '''
        Primary tox node:
        - create group chat
        - hand off on shutdown
        - Inherited base functions
    '''
    
    def __init__(self, data=None):
        self.primary = True
        ToxBase.__init__(self)
        # group chat room
        self.base_group_id = self.add_groupchat()
        self.register('authenticate', self.__cmd_authenticate__)
        self.register('join_chat', self.__cmd_join_chat__)

    def on_dht_connected(self):
        self.set_user_status(Tox.USERSTATUS_NONE)
    
    def stop(self):
        #if len(self.__peers__) > 0:
        #    self.send_message(self.__peers__[0], 'primary')
        ToxBase.stop(self)
 
    def __cmd_join_chat__(self, event):
        self.invite_friend(event.params['friend_id'], self.base_group_id)

    def __cmd_authenticate__(self, event):
        if event.params['friend_id'] not in self.__peers__:
            self.__peers__.append(event.params['friend_id'])
