from queue import Queue
import random
from warnings import warn
from threading import RLock, Timer
import traceback

import ujson

from rainmaker.net.utils import RTimer, LStore

class EventError(Exception):
    pass

class Params(object):
    '''
        Useful class for managing parameters
    '''
    def __init__(self, data=None):
        super(Params, self).__init__()
        self.data = {} if data is None else data
        if not type(self.data) is dict:
            raise EventError('Not a dictionary')
        self.akeys = set()
        self.rkeys = set()
    
    def __repr__(self):
        ''' Fancy lookin repr '''
        try:
            return '<%s %s>' % (self.__class__.__name__, ', '.join(['%s:%s' % (k, v) for k, v in self.data.items()]))
        except TypeError as e:
            return super(Params, self).__repr__()

    def require(self, *keys):
        '''Require these keys'''
        self.rkeys.update(keys)
        return self

    def allow(self, *keys):
        '''Allow these keys'''
        self.akeys.update(keys)
        return self
            
    def val(self, key=None):
        '''get req/allow keys or key'''
        try:
            if key is not None:
                return self.data[key]
            if not self.akeys and not self.rkeys:
                return self.data
            result = {}
            for k in self.rkeys:
                result[k] = self.data[k]
            for k in self.akeys:
                if k in self.data:
                    result[k] = self.data[k]
            return result
        except KeyError as e:
            raise EventError
        except TypeError as e:
            raise EventError

    def get(self, key):
        ''' Instantiate new from data '''
        try:
            val = self.data[key]
        except KeyError as e:
            raise EventError
        except TypeError as e:
            raise EventError
        return Params(val)

class Event(Params):
    '''
        Events that are generated by EventHandler
    '''
    def __init__(self, name, params=None, status=None, reply=None, error=None, \
            source=None, rcode=0):
        super(Event, self).__init__(params)
        self.name = name
        self.status = status if status else 'ok'
        self.source = source
        self.reply_with = reply
        self.error_with = error
        self.rcode = rcode 

    def reply(self, status, params=None):
        if not self.reply_with:
            warn('No "reply_with" specified for: %s' % self.name)
            return
        e = Event(self.rcode, params=params, status=status)
        self.reply_with(e)

class EventHandler(object):
    '''
        Listen for events and call registered functions
    '''
    def __init__(self, parent=None, queue=False):
        self.parent = parent
        self.__cmds__ = LStore()
        self.queue = Queue() if queue else None

    def call_event(self, name, **kwargs):
        '''
            Call all functions for event name
        '''
        kwargs['source'] = self.parent
        event = Event(name, **kwargs)
        try:
            funcs = self.__cmds__[event.name]
        except KeyError as e: 
            self.handler_missing(event)
            return False 
        if self.queue:
            self.queue.put((funcs, event))
        else:
            self.dispatch(funcs, event)
        return True

    def commit(self):
        '''Run all events in Queue'''
        while True:
            try:
                funcs, event = self.queue.get_nowait()
                self.dispatch(funcs, event)
            except Empty as e:
                break

    def dispatch(self, funcs, event): 
        ''' Run a single event '''
        try:
            for f in funcs:
                if f(event) == False:
                    return False
        except EventError as e:
            warn(traceback.format_exc())
            if event.error_with:
                event.error_with(e)
            return False
        return True

    def handler_missing(self, event):
        '''
            Method called when there are no registered handlers
        '''
        warn('Handler missing: %s' % event.name)

    def temp(self, func, timeout=30):
        ''' Register a temporary function '''
        return self.__cmds__.append([func], timeout=timeout)

    def register(self, name, func, timeout=0):
        '''
            Register func as function to be called when 
            event name is called
        '''
        arr = self.__cmds__.get(name, [])
        arr.append(func)
        return self.__cmds__.put(name, arr, timeout=timeout)

