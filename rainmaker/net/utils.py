from threading import RLock, Timer
import random

randint = random.randint
MAX_INT = 10**12

def new_key(adict):
    ''' Generate a random key for dictionary '''
    success = False
    while success != True:
        key = str(randint(0, MAX_INT))
        success = adict.get(key, True)
    return key

class LStore(object):
    '''
        Locking storage with optional timeout
    '''
    def __init__(self, timeout=0):
        self.timeout = timeout
        self._buffer = {}
        self.lock = RLock()
        self.put = self.__setitem__
 
    def __getitem__(self, key):
        with self.lock:
            timer, val = self._buffer[key]
            if timer:
                timer.reset()
        return val
    
    def get(self, key, default=None):
        with self.lock:
            timer, val = self._buffer.get(key, [None, default])
            if timer:
                timer.reset()
        return val

    def __setitem__(self, key, val, timeout=0):
        timer = None
        timeout = timeout if timeout else self.timeout
        with self.lock: 
            if timeout:
                timer = RTimer(timeout, self.pop, params=[key, True])
                timer.on()
            self._buffer[key] = (timer, val)
    
    def pop(self, key, from_timer=False):
        ''' Pop a key from dictionary '''
        with self.lock:
            timer, val =  self._buffer.pop(key, (None, None))
            if timer and not from_timer:
                timer.off()
                del(timer)

    def append(self, obj, timeout=0):
        ''' Add an item to storage '''
        with self.lock:
            key = new_key(self._buffer)
            self.put(key, obj, timeout)
        return key

class RTimer(object):
    '''
        Generic timer that will run after timeout elapsed
    '''
    def __init__(self, timeout, func, loop=False, params=None):
        self.fparams = params if params else []
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
        self.func(*self.fparams)
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

