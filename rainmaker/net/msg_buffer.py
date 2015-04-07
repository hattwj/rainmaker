from threading import RLock, Timer
import random
import math
from warnings import warn

import ujson

from rainmaker.net.utils import LStore

MAX_CHUNK = 1300

def json_decoder(msg):
    cmd_line, data = msg.split("\n", 1)
    del(msg)
    cmd, status = cmd_line.split(':', 2)
    data = None if not data else ujson.loads(data)
    return (cmd, status, data)

def string_line_parser(line):
    '''
        parse input from protocol
    '''
    hd_line, data = line.split("\n", 1)
    del(line)
    rcode, mno, mto = hd_line.split(':', 2)
    rcode = int(rcode)
    mno = int(mno)
    mto = int(mto)
    return rcode, mno, mto, data

def json_encoder(rcode, cmd, status, msg=None, chunk=MAX_CHUNK):
    ''' yield complete command '''
    # 
    if msg is not None:
        msg = ujson.dumps(msg)
    # convert empty message to empty string
    if msg is None:
        msg = ''
    # generate message
    msg = '%s:%s\n%s' % (cmd, status, msg)
    # calc available space
    _chunk = chunk - (len(str(rcode)) + 3)
    # yield message in parts
    for mno, mto, data in yield_parts(msg, _chunk):
        # yield part with header on first line
        yield (mno, mto, "%s:%s:%s\n%s" % (rcode, mno, mto, data))

def yield_parts(msg, chunk):
    ''' Yield parts of bitarr/string'''
    counter = 0
    # count how many parts in msg
    mcount = math.ceil(len(msg)/chunk) - 1
    _chunk = chunk - len(str(mcount))*2 
    assert _chunk > 0
    # yield each part
    for x in range(0, len(msg), _chunk):
        yield counter, mcount, msg[x:x+_chunk]
        counter += 1

class MessageBufferError(Exception):
    pass

'''
    rlen+mnlen+mtlen+3
    mb:
        serializer:
            json for now
            format:
                rcode:mno:mto\n
                cmd:status\n
                data
        send(event)
            - encode
            - add response key
            - yields data
        recv(data)
            - decode
            - remember response key
            - yields event when complete
'''
class MsgBuffer(object):

    def __init__(self, timeout=30, chunk=1300):
        self.chunk = chunk
        self._rbuff = LStore(timeout)
        self.encoder = json_encoder
        self.line_parser = string_line_parser
        self.decoder = json_decoder

    def send(self, rcode, cmd, status, data):
        ''' yield messages to send event '''
        for mno, mto, msg in self.encoder(rcode, cmd, status, data, chunk=self.chunk):
            # yield msg to send
            yield (mno, mto, msg)

    def recv(self, line):
        rcode, mno, mto, data = self.line_parser(line)
        del(line)
        buff = self._rbuff.get(rcode, None)
        if buff is None:
            buff = ArrBuffer(mto)
            self._rbuff.put(rcode, buff) 
        for _data in buff.insert(mno, data): 
            # yield complete message
            cmd, status, params = self.decoder(_data)
            yield (rcode, cmd, status, params)
                
class ArrBuffer(object):
    ''' Generic string/byte_arr buffer '''
    def __init__(self, count, binary=False):
        '''
            Init and add to cache
        '''
        self._seed = b'' if binary else ''
        self.lock = RLock()
        self._buffer = [None] * (count + 1)

    def insert(self, pos, msg):
        ''' Add part to msg
            - return full message when ready
        '''
        with self.lock:
            self._buffer[pos] = msg
            if None not in self._buffer:
                # yield full string when complete
                yield self._seed.join(self._buffer)
