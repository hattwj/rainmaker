'''
UDP P2P Multicast server
    - multicast for LAN discovery
    - announce loop
    - add new addr, port, pubkey combos
    - expire old ones
'''

# imports for everyone
from twisted.internet import reactor, defer
from twisted.application.internet import MulticastServer
from twisted.python import log

# imports for RequestParser
import json
import re
from threading import Lock
    
# Imports for protocol 
import errno
from socket import error as socket_error
from copy import deepcopy
from twisted.internet.protocol import DatagramProtocol
from .net_utils import is_compatible, get_address
from rainmaker_app.db.models import Host
from rainmaker_app.lib.util import assign_attrs, snake_case, time_now
from rainmaker_app import app, version
from rainmaker_app.lib.net import finger_table
from rainmaker_app.lib.net.clients import ClientFactory

class Param(object):
    
    def __init__(self, name, constructor, required):
        self.name = name
        self.param_type = param_type

    def construct(self):
        pass

class BaseResponder(object):
    params = None
    def __init__(self):
        self.errors = []
        if not self.params:
            self.params = []
        self.params_count = len(self.params)
        self.name = snake_case(
            self.__class__.__name__.replace('Responder','')
        )

    def run(self, request):
        raise NotImplementedError('Abstract method')

class PingResponder(BaseResponder):
    def run(self, request):
        print app.auth.to_json()
        
class StoreValueResponder(BaseResponder):
    params = ['key','value']
    def run(self, request):
        request.dht.update_host(request.host)
        request.dht.store(
            request.params['key'],
            request.params['value']
        )
class StoreHostResponder(BaseResponder):
    def run(self, request):
        pass

class FindHostResponder(BaseResponder):
    params = ['key']
    def run(self, request):
        request.dht.update_host(request.host)
        def on_host_found(self, host):
            params = {
                'address': host.address,
                'tcp_port': host.tcp_port,
                'udp_port': host.udp_port,
                'pubkey': host.pubkey,
                'signature': host.signature,
                'timestamp': host.timestamp
            }
            request.transport.send('store_host', **params)
        request.dht.find_host(request.params['key'], on_host_found)
        
class FindValueResponder(BaseResponder):
    params = ['key'] 
    
    def on_value_found(self, key, value):
        request.transport.send('store_value', key=key, value=value)

    def run(self, request):
        request.dht.update_host(request.host)
        request.dht.find_value(request.params['key'], on_value_found)

DEFAULT_ACTIONS = [
    PingResponder(),
    StoreHostResponder(),
    StoreValueResponder(),
    FindHostResponder(),
    FindValueResponder()
]

class RequestEncoder(object):
    '''
        UDP multipart Datagram encoder with recall
    '''
    

    # class properties
    mtu = 500 # bytes
    msg_ttl = 5 # seconds
    fidmax = 1 * 10**6 # frame ids
    __fid = 0
    __fid_lock = Lock()
    __buffer = {}
    __buffer_lock = Lock()

    def __init__(self, addr_port, action, msg=None):
        if len(action) > 50:
            raise AttributeError('Action name too large')
        # class instance properties
        self.fid = None
        self.__fmax = None
        self.__atu = None
        self.__prefix = None
        self.address, self.port = addr_port
        self.msg = msg
        self.action = action    
        self.msg_len = len(msg) if msg else 0

    def iter_messages(self, fno=None, num=None):
        '''
            Encode all messages and yield them one at a time
        '''
        if not self.msg:
            yield self.prefix
            raise StopIteration
        fno = fno if fno else 0
        num = num if num else self.fmax + 1
    
        if not self.fid:
            self.__class__.store(self) 
        result = self.calc_step_params(fno, num) 
        lbound, ubound, fno = result
        prefix, fmax = self.prefix, self.fmax
        step_size = self.atu
        #print [lbound,ubound,step_size,len(self.msg), self.fmax]
        for i in range(lbound, ubound, step_size):
            msg_part = self.msg[i:i+step_size]
            chunk = "%s:%s:%s:%s" % (prefix, fno, fmax, msg_part)
            yield chunk
            fno += 1
        raise StopIteration
    
    @property
    def prefix(self):
        '''
            generate packet header
        '''
        if self.__prefix:
            return self.__prefix
        self.__prefix = 'rain%s%s%s' % (version, self.action, self.fid)
        # check for errors
        if len(self.__prefix) >= self.mtu:
            raise AttributeError('command too large')
        return self.__prefix
     
    @property
    def fmax(self):
        '''
            Calculate the number of frames for message
        '''
        if self.__fmax:
            return self.__fmax
        self.__fmax = int(round(len(self.msg) / (self.mtu - len(self.prefix) + 3.0)))
        return self.__fmax
    
    @property
    def atu(self):
        '''
            Calculate Available Transfer Units
        '''
        if self.__atu:
            return self.__atu
        # estimate available space after overhead
        self.__atu = self.mtu - (3 + len(self.prefix) + len(str(self.fmax))*2)    
        return self.__atu

    def calc_step_params(self, fno, num):
        '''
            calc lbound ubound fno for msg
        '''
        if fno > self.fmax:
            fno = fmax
        
        # calculate bounds 
        lbound = fno*self.atu
        ubound = (fno+num)*self.atu 
        ubound = len(self.msg) if ubound > len(self.msg) else ubound

        # return bounds and prefix
        return [lbound, ubound, fno]

    @classmethod
    def store(klass, encoder):
        '''
            Store encoder by fid
        '''
        encoder.fid = fid = klass.get_fid() 
        klass.__buffer_lock.acquire()
        klass.__buffer[fid] = encoder
        app.reactor.callLater(klass.msg_ttl, klass.remove, fid)
        klass.__buffer_lock.release() 
    
    @classmethod
    def find(klass, fid):
        '''
            Find encoder by fid
        '''
        result = None 
        klass.__buffer_lock.acquire()
        if fid in klass.__buffer:
            result = klass.__buffer[fid]
        klass.__buffer_lock.release()
        return result
    
    @classmethod
    def remove(klass, key):
        '''
            Remove val by key
        '''
        klass.__buffer_lock.acquire()
        if key in klass.__buffer:
            del(klass.__buffer[key])
        klass.__buffer_lock.release()
    
    @classmethod
    def buffer_debug(klass):
        '''
           not thread safe, debug only 
        '''
        return klass.__buffer
    
    @classmethod
    def buffer_wipe(klass):
        '''
            Delete all keys in buffer and reset
        '''
        klass.__buffer_lock.acquire()
        klass.__buffer = {}
        klass.__buffer_lock.release() 

    @classmethod
    def get_fid(klass):
        '''
            Get a frame id 
        '''
        klass.__fid_lock.acquire()
        klass.__fid = (klass.__fid + 1) % klass.fidmax
        klass.__fid_lock.release()
        return klass.__fid

class RequestParser(object):
    '''
        Parse/encode datagrams 
    '''
    # class properties
    dht=None
    transport=None
    actions = DEFAULT_ACTIONS
    
    __buffer = {}
    __buffer_lock = Lock()
    buffer_ttl = 5 # seconds

    # protocol error codes
    ERR_NONE        = None  # No errors occurred
    ERR_INCOMPLETE  = 1     # Datagram not yet complete
    ERR_BUFFER      = 2     # this request's buffer is disabled
    ERR_EXPIRED     = 3     # datagram expired
    ERR_SELF        = 6     # datagram from self
    ERR_EMPTY       = 7     # empty datagram received
    ERR_PROTOCOL    = 8     # invalid protocol ident
    ERR_MALFORMED   = 9     # no version specified
    ERR_VERSION     = 10    # incompatible version
    ERR_ACTION      = 11    # unknown command specified
    ERR_FRAME       = 12    # packet frame error
    ERR_PARAMS      = 13    # param count mismatch
    
    #
    #                      app  version        action        fid   fno   fmax  data
    #pattern = re.compile('^rain(\d+\.\d+\.\d+)([a-z_]+)?((\d+):(\d+):(\d+):(.*))')
    pattern = re.compile('^rain(\d+\.\d+\.\d+)([a-z_]+)((\d+):(\d+):(\d+):(.*))?')
    app_key = 'rain%s' % (version)    
    version = None
    data = None
    action = None
    fid = None
    fno = None
    fmax = None
    error = None

    __responder = None
    __datagrams = None
    __params = None
 
    @classmethod
    def parse(klass, addr_port, datagram):
        request = klass(addr_port, datagram)
        return request.buffer_sync()

    def __init__(self, addr_port, datagram):
        self.ran = False
        self.timestamp = time_now()
        self.address, self.port = addr_port
        self.error = self.__parse__(datagram)

    @property
    def datagrams(self):
        '''
            init if needed, return datagrams
        '''
        if self.__datagrams:
            return self.__datagrams            
        if not self.is_multipart:
            return self.__datagrams
        # init datagrams
        self.__datagrams = [None for x in range(0,self.fmax+1)]
        return self.__datagrams
    
    @property
    def params(self):
        if not self.__params:
            self.__params = ''.join(self.datagrams)
        return self.__params

    @property
    def is_multipart(self):
        return self.fmax != None
    
    @property
    def is_ready_to_run(self):
        if self.error and self.error != self.ERR_INCOMPLETE:
            return False
        if self.ran:
            return False
        if not self.is_multipart:
            return True
        if None in self.datagrams:
            self.error = self.ERR_INCOMPLETE
            return False
        else:
            self.error = self.ERR_NONE
            return True

    @property
    def transport(self):
        raise NotImplementedError('Abstract class property not set')
    
    @property
    def dht(self):
        raise NotImplementedError('Abstract class property not set')

    def __parse__(self, datagram):
        '''
            Parse datagram and set variables
        '''
        if not datagram:
            return self.ERR_EMPTY
        match = self.pattern.match(datagram)
        if not match:
            return self.ERR_PROTOCOL
        # extract base information about request
        self.ver, self.action, sub_match, fid, fno, fmax, data = match.groups()
        # check version
        if not is_compatible(self.ver):
            return self.ERR_VERSION
        if not self.responder:
            return self.ERR_ACTION
        if sub_match:
            self.fid = int(fid)
            self.fno = int(fno)
            self.fmax = int(fmax)
            if self.fno > self.fmax:
                return self.ERR_FRAME
            self.data = data 
        return self.ERR_NONE

    def buffer_sync(self):
        '''
            sync with message buffer
        '''
        if not self.is_multipart:
            return self
        if self.error and self.error != self.ERR_INCOMPLETE:
            return self
        return self.__class__.buffer_add(self)

    def buffer_name(self):
        '''
            generate key for __buffer
        '''
        return '%s.%s.%s' % (self.address, self.port, self.fid)
    
    def buffer_insert(self, request):
        '''
            add data from this request to our __datagrams
        '''
        if not self.datagrams[request.fno]:
            self.timestamp = time_now()
            self.datagrams[request.fno] = request.data
    
    def buffer_ignore(self):
        '''
            the request buffer said this request
            should be ignored
        '''
        self.error = self.ERR_BUFFER
    
    @classmethod
    def buffer_add(klass, request):
        '''
            check to see if this request is multipart
            returns request or multipart request
        '''
        klass.__buffer_lock.acquire()
        name = request.buffer_name()
        if name in klass.__buffer:
            # add data to multipart request
            buf_request = klass.__buffer[name]
            if buf_request:
                # insert datagram
                buf_request.buffer_insert(request)
                if buf_request.is_ready_to_run:
                    # remove from buffer if complete
                    klass.__buffer[name] = None
                request = buf_request
            else:
                # name was in dict, but no object
                # were in refractory phase
                # will end with buffer_del
                request.buffer_ignore()
        else:
            # were not in the buffer yet
            klass.__buffer[name] = request          # add to buffer
            request.error = request.ERR_INCOMPLETE  # mark incomplete
            request.buffer_insert(request)          # add datagram
            # set expiration timer callback
            app.reactor.callLater(klass.buffer_ttl, klass.buffer_del, request)
        klass.__buffer_lock.release()
        return request

    @classmethod
    def buffer_del(klass, request):
        '''
            delete a request in buffer if expired
        '''
        klass.__buffer_lock.acquire()
        name = request.buffer_name() 
        if name in klass.__buffer:
            buf_request = klass.__buffer[name]
            # remove
            if buf_request == None or request.expired():
                del(klass.__buffer[name])    
            else:
                app.reactor.callLater(klass.buffer_ttl, klass.buffer_del, request)
        klass.__buffer_lock.release()
    
    @classmethod
    def buffer_wipe(klass):
        '''
            wipe all buffers
        '''
        klass.__buffer_lock.acquire()
        klass.__buffer = {}
        klass.__buffer_lock.release()

    @property
    def responder(self):
        '''
            Find the responder class for our action
        '''
        if self.__responder:
            return self.__responder
        for action in self.actions:
            if action.name == self.action:
                self.__responder = action
                break
        return self.__responder

    def run_responder(self):
        '''
            Run responder if it is ready
        '''
        if self.is_ready_to_run:
            self.ran = True
            self.responder.run(self)
        return self.responder.errors

    def expired(self):
        '''
            See if buffer_ttl has been exceeded
        '''
        msecs =  time_now() - self.timestamp 
        return msecs/1000 > self.__class__.buffer_ttl

class HostsFilter(object):
    '''
        Filter messages, only accept one message per host
    '''
    def __init__(self):
        self.__filter__ = []
        self.lock = Lock()

    def add(self, request):
        '''
            Add a host if not present
        '''
        key = '%s:%s:%s' % (request.address, request.udp_port, request.tcp_port)
        kwargs = {
            'address' : request.address,
            'udp_port' : request.udp_port,
            'tcp_port' : request.tcp_port
        }
        host = None
        self.lock.acquire()
        if not key in self.__filter__:
            host = Host( **kwargs)
            self.__filter__.append(key)
        self.lock.release()
        return host
     
    def clear(self):
        ''' clear cache '''
        self.lock.acquire()
        self.__filter__ = []
        self.lock.release()

class MulticastServerUDP(DatagramProtocol):
    '''
        Lan discovery server            
    '''
    # protocol error codes
    ERR_NONE        = None  # No errors occurred
    ERR_SELF        = 1     # datagram from self
    ERR_PARSER      = 10    # unable to parse datagram
    ERR_FUNC        = 20    # command failed

    # Default configuration 
    multicast_group = '224.0.0.0'
    listen_port = 8500    
    broadcast = True
    broadcast_port = 8500
    min_interval = 1
    max_interval = 10
    pattern = re.compile('^rain:(\d+\.\d+\.\d+):([a-z\.\d]+):([\d\.]+):(\d+):(.*)')

    # private variables
    __address__ = None              # set later
    __broadcast_msg__ = None

    def __init__(self, **kwargs):
        assign_attrs(self, **kwargs)
        self.hosts_filter = HostsFilter()
    
    @property
    def addr_port(self):
        return (app.server.address, self.listen_port,)

    def start(self):
        ''' start multicast server '''
        # Optionally override attributes
        RequestParser.transport = self
        RequestParser.dht = self.dht
        app.reactor.listenMulticast(self.listen_port, self)
        app.udp_server.broadcast_loop()
        log.msg( 'UDP server listening on port %s' % self.listen_port) 
        log.msg('UDP broadcasting on port %s' % self.broadcast_port)
        
    ###############################################
    # Protocol Parser
    ###############################################
    def datagramReceived(self, datagram, addr_port):

        # filter datagrams from self
        if addr_port == self.addr_port:
            return self.ERR_SELF
        
        # process datagram
        #request = RequestParser.parse(addr_port, datagram)

        # run command
        #request.run_responder()
        match = self.pattern.match(datagram)
        if match:
            ver, addr, tcp_port, udp_port, sig = match.groups()
            if addr == 'self':
                addr = addr_port[0]
            if not is_compatible(ver):
                return
            host_params = {
                'ver': ver,
                'address': addr,
                'tcp_port': int(tcp_port),
                'udp_port': int(udp_port),
                'signature': sig
            }
            host = Host(**host_params)
            if not finger_table.exists(host):
                print host
                print 'host added'
                finger_table.add(host)
        return
     
    ###########################################
    # Protocol Command Senders
    ###########################################
    def send_message(self, addr_port, msg):
        '''
            send a message to host
        '''
        #request = RequestEncoder(addr_port, action, msg)
        #for msg in request.iter_messages():
        err = self.__send(addr_port, msg)
        return err
    
    def __send(self, addr_port, msg):
        ''' send a message '''
        try:
            self.transport.write(msg, addr_port)
        except socket_error as serr:
            # is the muticast unreachable?
            if serr.errno != errno.ENETUNREACH:
                # Not the error we are looking for, re-raise
                raise serr
            log.msg( 'Network unreachable')
            app.server.setup_host()
            return True
        return False

    def broadcast_loop(self):
        ''' announce presence on lan '''
        interval = self.min_interval
        # Send multicast announce message
        addr_port = (self.multicast_group, self.broadcast_port,) 
        err = self.send_message(addr_port, self.ping_msg())
        if err:
            # wait for loop because of error
            interval = self.max_interval
        if self.broadcast == True:
            app.reactor.callLater(interval, self.broadcast_loop)
    
    ###########################################
    # Server Utility Functions
    ###########################################
 
    def ping_msg(self):
        return 'rain:%s:%s:%s:%s:%s' % (version, 'self', app.server.listen_port, self.listen_port, app.server.host.signature )

    def ping(self, addr_port):
        return self.send_message(addr_port, self.ping_msg())

    def startProtocol(self):
        # Join a specific multicast group, which is the IP we will respond to
        self.transport.joinGroup(self.multicast_group)
        self.check_address()

    def check_address(self):
        ''' check that address is set '''
        # get our ip addr for filtering msgs from self
        if not self.__address__:
            self.hosts_filter.clear()
            self.__address__ = get_address()
            log.msg('Our address is: %s' % self.__address__)
    
    @property
    def client_factory(self):
        '''
            Override this with a Client Factory
        '''
        raise NotImplementedError('Abstract property')
    
    @property
    def dht(self):
        '''
            Override this with a dht
        '''
        raise NotImplementedError('Abstract property')

    def on_new_host(self, host):
        '''
            Override this with an event listener
        '''
        raise NotImplementedError('Abstract method, override')

