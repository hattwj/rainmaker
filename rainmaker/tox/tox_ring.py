# stdlib imports
from __future__ import print_function
from warnings import warn
from threading import Thread, Timer
from time import sleep

# lib imports
import ujson
from pytox import Tox, OperationFailedError

# local imports
from rainmaker.main import Application
from rainmaker.tox import tox_env
from rainmaker.tox import tox_errors

from rainmaker.net.events import Event, EventHandler, Params, EventError


def parse(line):
    '''
        parse yaml input from tox client
    '''
    try:
        request = ujson.loads(line)
    except ValueError as e:
        raise tox_errors.ToxCommandError('Failed to parse request')
    if not isinstance(request, dict):
        raise tox_errors.ToxCommandError('Request not a dictionary')
    cmd = request.get('command', None)
    if cmd is None:
        raise tox_errors.ToxCommandError('No command given')
    params = request.get('params', {})
    if not isinstance(params, dict):
        raise tox_errors.ToxCommandError('Params not a dictionary')
    
    return [cmd, params]

class ToxTimer(object):
    '''
        Generic timer that will run after timeout elapsed
    '''
    def __init__(self, timeout, func, loop=False):
        self.timeout = timeout
        self.func = func
        self.loop = loop
        self._timer = None
        self.ran = False
        self.started = False

    @property
    def running(self):
        '''
            Is the timer running?
        '''
        return self.started and not self.ran

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
        self._timer = Timer(self.timeout, self._run)
        self._timer.daemon = True
        self._timer.start()
        self.ran = False
        self.started = True
        
    def off(self):
        '''
            Turn the timer off
        '''
        
        self._timer.cancel()

    def is_alive(self):
        return self._timer is not None and self._timer.is_alive()

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

class RunLevel(object):
    '''
        Generic run_level for state machine
    '''
    def __init_vars__(self):
        '''
            Initialize vars
        '''
        self.running = False
        self.should_run = True
        self.should_wait = True
        self.valid = False
        self.action = None
        self.prev_action = None

    def __init__(self, name, startf, stopf, validf, timeout=30, rate=0.5):
        ''' 
            
        '''
        self.name = name 
        self.__start = startf
        self.__stop = stopf
        self.__valid = validf
        self.__init_vars__()
        self.timeout = timeout
        self.rate = rate
    
    @property
    def status_changed(self):
        '''
            Has status changed?
        '''
        return self.prev_action != self.action

    def loop(self):
        '''
            Do loop once and record result
        '''
        self.prev_action = self.action
        self.action = self.__loop__()
        return self.action

    def __loop__(self):
        '''
            Do loop once and return result
        '''
        if self.running and self.should_run:
            if self.valid:
                return StateMachine.DO_NEXT
            elif self.should_wait:
                return StateMachine.DO_WAIT
            else:
                self.restart()
                return StateMachine.DID_RESTART
        elif self.running and not self.should_run:
            self.stop()
            return StateMachine.DID_STOP
        elif not self.running and self.should_run:
            self.start()
            return StateMachine.DID_START
        else:
            return StateMachine.DID_NO_OP
    
    def restart(self):
        '''
            Restart level
        '''
        self.stop()
        return self.start()

    def start(self):
        '''
            Start level
        '''
        def _stop_waiting():
            self.should_wait = False
        self.should_wait = True
        self.__init_vars__()
        self.__start()
        # start timeout timer
        self.__timeout_timer = ToxTimer(self.timeout, _stop_waiting)
        self.__timeout_timer.on()
        # start validity rate timer
        self.__rate_timer = ToxTimer(self.rate, self.__is_valid__, loop=True) 
        self.__rate_timer.on()
        self.running = True

    def stop(self):
        '''
            Stop level
        '''
        self.__stop()
        self.__rate_timer.off()
        self.__timeout_timer.off()
        self.running = False

    def __is_valid__(self):
        '''
            Check for valid state
        '''
        self.valid = self.__valid()
        if self.valid and self.__timeout_timer.running:
            self.__timeout_timer.off()
        elif not self.valid and not self.__timeout_timer.running:
            self.__timeout_timer.on()
        return self.valid

class StateMachine(object):
    DID_NO_OP   = -1
    DID_STOP    = 0
    DID_START   = 1
    DO_WAIT     = 2
    DID_RESTART = 3
    DO_NEXT     = 4
    
    # Filter out these events
    IGNORES = [DID_NO_OP, DO_WAIT]#, DO_NEXT]

    ACTION_NAMES = {
        DID_NO_OP:    'ignoring' ,
        DID_STOP:     'stopping',
        DID_START:    'starting',
        DO_WAIT:      'lost',
        DID_RESTART:  'restarting',
        DO_NEXT:      'completed'
    }

    def __init__(self, wait_time=0.5):
        self.run_levels = []
        self.wait_time = wait_time
     
    def start(self):
        '''
            start state machine
            - does not block
        '''
        self.stopping = False
        self.do_next = True
        self.__start_loop = Thread(target=self.__loop__)
        self.__start_loop.daemon = True
        self.__start_loop.start()
        return self.__start_loop
    
    def __loop__(self):
        while True:
            if self.stopping and not self.any_running:
                # were done
                print('Done')
                break
            self.__loop_once__()
            sleep(self.wait_time)

    def __loop_once__(self):
        self.do_next = not self.stopping
        for idx, run_level in enumerate(self.run_levels):
            run_level.should_run = self.do_next 
            action = run_level.loop()
            if run_level.status_changed and not self.level_filter(action):
                self.level_changed(run_level.name, run_level.action, run_level.prev_action)
            if action != self.DO_NEXT:
                self.do_next = False
                levels = []
                for jdx, level in enumerate(self.run_levels):
                    if jdx > idx and level.running:
                        levels.append(level)
                for level in reversed(levels):
                    level.should_run = False
                    level.loop()
                return
            else:
                self.do_next = True
    
    def level_filter(self, action):
        '''
            Override to change filter behavior
        '''
        return action in self.IGNORES

    def level_changed(self, name, action, prev_action):
        '''
            Override to receive level changed event
        '''
        print('%s %s' % (self.ACTION_NAMES[action], name))

    @property
    def any_running(self):
        '''
            Are any run_levels running?
        '''
        for level in self.run_levels:
            if level.running:
                return True
        return False

    def add(self, run_level):
        '''
           Add run Level 
        '''
        if not hasattr(run_level, 'should_run'):
            raise AttributeError('Not a run level')
        self.run_levels.append(run_level)

    def stop(self):
        '''
            signal stop
        '''
        self.stopping = True
    
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
        self.__pong = Event('pong').serialize()
    
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

    def on_friend_request(self, pk, message):
        '''
            Pass to authenticate
        '''
        cmd, params = parse(message)
        params['friend_id'] = None
        params['friend_pk'] = pk
        cmd = 'authenticate'
        self.router.call_event(cmd, **params)

    def on_friend_message(self, friend_id, message):
        '''
            A friend has sent a message
        '''
        cmd, params = parse(message)
        params['friend_id'] = friend_id
        self.router.call_event(cmd, **params)

    def on_group_message(self, group_number, friend_id, message):
        '''
            A group member sent a message
        '''
        cmd, params = parse(message)
        params['friend_id'] = friend_id
        params['group_number'] = group_number
        self.router.call_event(cmd, **params)

    def send_fs_event(self, event):
        '''
            Broadcast fs_event
        '''
        message = event.serialized_params()
        self.group_message_send(self.base_group_id, message)
        raise NotImplementedError('wip') 

    def __cmd_ping__(self, event):
        fid = event.val('friend_id')
        self.send_message(fid, self.__pong)

class SyncBot(ToxBase):
    '''
        Find primary bot and relay information or bail
        if timeout reached
    '''
    def __init__(self, primary_bot, data=None):
        ToxBase.__init__(self, data)
        self.router.register('fs_event', self.__cmd_fs_event__)
        self.router.register('get_host', self.__cmd_get_host__)
        self.router.register('put_host', self.__cmd_put_host__)
        self.router.register('primary', self.__cmd_primary__)
        self.primary = False
        self.primary_bot = primary_bot
        self.state_machine.add(self.__search_run_level__())
        self.__host = Event('put_host', pubkey=self.get_address(), 
            device_name=Application.device_name,
            version=Application.version).serialize()
        
    def __search_run_level__(self):
        
        #self.__search_tries_left = 2
        auth_msg = Event('authenticate').serialize()
        ping_msg = Event('ping').serialize()
        
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
                        self.send_message(fid, ping_msg)
                except OperationFailedError as e:
                    pass
                return False
        
        return RunLevel('tox_search', _start, _stop, _valid, 40)

    def on_group_invite(self, friend_num, gtype, grp_pubkey):
        print('Joining group: %s' % gtype)
        group_id = self.join_groupchat(friend_num, grp_pubkey)
             
    @require_auth
    def __cmd_fs_event__(self, event):
        '''
            Someone had a file_system event
        '''
        pass
    
    @require_auth
    def __cmd_primary__(self, event):
        '''
            Someone thinks we should be primary
        '''
        fpk = event.val('friend_pk')
        # Only listen to primary
        if fpk == self.primary_bot.get_address():
            self.primary_bot.start()

    @require_auth
    def __cmd_get_host__(self, event):
        '''
            Someone wants our host info
        '''
        fid = event.val('friend_id')
        self.send_message(fid, self.__host)
    
    @require_auth
    def __cmd_put_host__(self, event):
        ''' Save host information '''
        params = event.get('host').require('pubkey', 'device_name').val()
        params['sync_id'] = self.sync.id
        host = Host(**params)

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
        self.router.register('authenticate', self.__cmd_authenticate__)
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

    def __cmd_authenticate__(self, event):
        '''
            TODO: implement tox authorization logic
        '''
        fid = event.val('friend_id')
        fpk = event.val('friend_pk')
        self.__authenticated_friends__.add(fid)
        self.add_friend_norequest(fpk)
        
