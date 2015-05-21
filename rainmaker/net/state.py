from threading import Thread
from time import sleep

from rainmaker.net.utils import RTimer

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
        self.__timeout_timer = RTimer(self.timeout, _stop_waiting)
        self.__timeout_timer.on()
        # start validity rate timer
        self.__rate_timer = RTimer(self.rate, self.__is_valid__, loop=True) 
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

