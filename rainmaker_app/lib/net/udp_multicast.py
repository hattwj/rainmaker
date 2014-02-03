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

# imports for DatagramParser
import json
import re
from threading import Lock
    
# Imports for protocol 
import errno
from socket import error as socket_error
from copy import deepcopy
from twisted.internet.protocol import DatagramProtocol
from .net_utils import is_compatible, get_address
from .commands import PingHostCommand
from rainmaker_app.db.models import Host
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app import app

class DatagramParser(object):
    '''
    Parse a datagram 
    '''
    # protocol error codes
    ERR_NONE        = None  # No errors occurred
    ERR_SELF        = 1     # datagram from self
    ERR_EMPTY       = 2     # empty datagram received
    ERR_PROTOCOL    = 3     # invalid protocol ident
    ERR_MALFORMED   = 9     # no version specified
    ERR_VERSION     = 10    # incompatible version
    ERR_ACTION      = 11    # unknown command specified  
    ERR_ARGS        = 12    # missing arguments

    pattern = re.compile('^rain:(\d+\.\d+\.\d+),([a-z_]+)?:?(.*)')
    app_key = 'rain:%s' % (app.version)
    
    version = None
    action = None
    datagram = None
    error = None

    actions = {
        'announce': ['tcp_port']
    }
    
    def __init__(self, addr_port, datagram):
        self.datagram = datagram
        self.error = self.__parse__(datagram)
        self.address = addr_port[0]
        self.udp_port = addr_port[1]
    
    @classmethod
    def encode(self, action, **kwargs):
        ''' encode a datagram and return it as a string ''' 
        return '%s,%s:%s' % (self.app_key, action, json.dumps(kwargs))

    def __parse__(self, datagram):
        if not datagram:
            return self.ERR_EMPTY
        data = self.pattern.match(datagram)
        if not data:
            return self.ERR_PROTOCOL
        # extract base information about request
        self.ver, self.action, self.data = data.groups()
        if not is_compatible(self.ver):
            return self.ERR_VERSION
        # check to see if action exists
        if not self.action in self.actions.keys():
            return self.ERR_ACTION
        # no more processing needed if there are no parameters
        if len(self.actions[self.action]) == 0:
            return self.ERR_NONE
        # process parameters
        params = json.loads(self.data)
        if type(params) != dict:
            return self.ERR_MALFORMED
        # test parameters
        for k in self.actions[self.action]:
            if k not in params.keys():
                return self.ERR_ARGS
        # set parameters
        for k in self.actions[self.action]:
            setattr(self, k, params[k])
        return self.ERR_NONE

class HostsFilter(object):
    def __init__(self, protocol):
        self.__filter__ = []
        self.lock = Lock()
        self.protocol = protocol

    def add(self, request):
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

    # private variables
    __address__ = None              # set later
    __broadcast_msg__ = None

    def __init__(self, **kwargs):
        # Optionally override attributes
        assign_attrs(self, **kwargs)
        # create announce command handler
        self.hosts_filter = HostsFilter(self)
    
    @property
    def addr_port(self):
        return (app.server.address, self.listen_port,)

    def start(self):
        ''' start multicast server '''
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
        request = DatagramParser(addr_port, datagram)
        if request.error: return self.ERR_PARSER

        # run command
        status = getattr(self, "%s_command" % request.action)(request)
        return self.ERR_NONE
    
    ###############################################
    # Protocol Command Responders
    ###############################################
    def announce_command(self, request):
        ''' check to see if new host '''
        host = self.hosts_filter.add( request )
        if not host:
            return
        app.client.ping_host((host.address, host.tcp_port,))

    ###########################################
    # Protocol Command Senders
    ###########################################
    def send_message(self, addr_port, action, **kwargs):
        msg = DatagramParser.encode(action, **kwargs)
        return self.send(addr_port, msg)
    
    def send(self, addr_port, msg):
        ''' send a message '''
        try:
            self.transport.write(msg, addr_port)
        except socket_error as serr:
            # is the muticast unreachable?
            if serr.errno != errno.ENETUNREACH:
                # Not the error we are looking for, re-raise
                raise serr
            print 'Network unreachable'
            app.server.setup_host()
            return True
        return False

    def broadcast_loop(self):
        ''' announce presence on lan '''
        interval = 0.5
        # Send multicast announce message
        addr_port = (self.multicast_group, self.broadcast_port,) 
        err = self.send_message(addr_port, 'announce', tcp_port=app.server.listen_port)
        if err:
            # wait for loop because of error
            interval = 5
        if self.broadcast == True:
            app.reactor.callLater(interval, self.broadcast_loop)
    
    ###########################################
    # Server Utility Functions
    ###########################################
    @property
    def addr_port(self):
        return (self.__address__, self.listen_port,)
 
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
    
    @property
    def client_factory(self):
        raise NotImplementedError('Must set tcp client factory')
