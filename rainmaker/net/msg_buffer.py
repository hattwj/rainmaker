from threading import RLock, Timer
import math
from warnings import warn

import ujson

'''
    cmd, mno, mto, format, tpk, ucid
    - p.call_w_reply
    - t.send
    - eh.register_temp
    - sb.split
    - t.tox_send
    - rt.tox_recv
    - rb.join
    - eh.add_reply
    - eh.call
    - c.run
    - c.reply
    - reh.call
    - rt.send
    - t.recv
    - eh.call_temp

    ucid protections:
    - unique eh per conn
'''

MAX_CHUNK = 1300

def recv_buffer(key, line):
    '''
        Load data into buffer
        - raise callback if ready
    '''
    cmd, mno, mto, data = parse(line)
    if mto > 0:
        if mno == 0:
            mbuf = MessageBuffer(key, mto)
        else:
            mbuf = MessageBuffer.find(key)
        if mbuf is None:
            warn('No buffer found')
            return
        data = mbuf.add(mno, data)
            
    if data is not None:
        data = ujson.loads(data)

    if mto == 1 or data is not None:
        yield cmd, data

def parse(line):
    '''
        parse input from protocol
    '''
    cmd_line, data = line.split("\n", 1)
    del(line)
    cmd, mno, mto = cmd_line.split(':', 2)
    mno = int(mno)
    mto = int(mto)
    return cmd, mno, mto, data

def send_buffer(cmd, msg=None, chunk=MAX_CHUNK, reply=None):
    ''' yield complete command '''
    if msg is not None:
        #msg = packb(msg, encoding='UTF-8')
        msg = ujson.dumps(msg)
    for mno, mto, data in string_buffer(msg, chunk):
        yield "%s:%s:%s\n%s" % (cmd, mno, mto, data)

def string_buffer(msg, chunk):
    ''' Yield string parts '''
    counter = 0
    if msg is None:
        msg = ''
    mcount = math.ceil(len(msg)/chunk) - 1
    for x in range(0, len(msg), chunk):
        yield counter, mcount, msg[x:x+chunk]
        counter += 1

class MessageBufferError(Exception):
    pass

class MessageBuffer(object):
    ''' Generic string message buffer '''
    __buffers__ = {}
    _block = RLock()

    @classmethod
    def find(klass, key):
        ''' Find buffer '''
        with klass._block:
            return klass.__buffers__.get(key, None)

    def __init__(self, key, count, timeout=30):
        '''
            Init and add to cache
        '''
        with self.__class__._block:
            if key in self.__class__.__buffers__:
                raise MessageBufferError('Key Exists: %s' % key)
            self.__class__.__buffers__[key] = self
        self.key = key
        self.lock = RLock()
        self._buffer = [None] * (count + 1)
        self._timer = Timer(timeout, self._pop)
        self._timer.daemon = True
        self._timer.start()

    def add(self, pos, msg):
        with self.lock:
            self._buffer[pos] = msg
            if None in self._buffer:
                return None
            else:
                self._pop()
                return ''.join(self._buffer)
    
    def _pop(self):
        block = self.__class__._block
        buffers = self.__class__.__buffers__
        with block:
            buffers.pop(self.key, None)
