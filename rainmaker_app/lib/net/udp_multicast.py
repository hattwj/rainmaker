'''
UDP P2P Multicast server
    - multicast for lan discovery
    - announce loop
    - add new addr, port, pubkey combos
    - expire old ones
'''

# imports for everyone
from twisted.internet import reactor, defer
from twisted.application.internet import MulticastServer
from rainmaker_app import app

# imports for DHTNode
from threading import Lock
from math import log
from rainmaker_app.db.models import Host, Authorization
import re
    
# Imports for protocol 
import errno
from socket import error as socket_error
from copy import deepcopy
from twisted.internet.protocol import DatagramProtocol
from .net_utils import is_compatible, get_address

# imports for DatagramParser
import json
import re

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
    
    ver = None
    action = None
    data = None
    error = None
    host = None

    actions = {
        'store': ['key','val'],
        'find': ['key'],
        'store_host': ['pubkey','address','port','signature', 'nonce'],
        'shutdown_host': ['signature', 'key', 'nonce'],
        'ping': []
    }
    
    def __init__(self, addr_port, datagram):
        self.error = self.__parse__(datagram)
        if not self.error:
            addr, port = addr_port
            self.host = Host(address=addr, udp_port=port)
    
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
    
class MulticastServerUDP(DatagramProtocol):
    '''
        
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
    
    address = None              # set later

    def __init__(self, **kwargs):
        node_args = kwargs.pop('node', {})
        # Optionally override attributes
        self.assign_attrs(**kwargs) 
        # Configure resources
        self.node = DHTNode(self, **node_args)

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
    def store_command(self, request):
        ''' Store a k/v pair '''
        added = self.node.store(request.host, request.key, request.val)
        return added

    def find_command(self, request):
        ''' Check to see if we have any matches '''
        found = self.node.find(request.host, request.key)
        return found

    def store_host_command(self, request):
        ''' add host info '''
        rhost = Host(address=request.address, 
            udp_port=request.udp_port,
            tcp_port=request.tcp_port,
            nonce = request.nonce,
            signature=request.signature,
            )
        added = self.node.store_host(request.host, rhost)

        return added

    def ping_command(self, request):
        ''' reply to ping command with a store host response '''
        return self.send_message(request.host, 'store_host', pubkey=self.host.pubkey, 
            address=self.host.address, port=self.host.udp_port, signature=self.host.signature)
    
    def shutdown_notify_command(self, request):
        ''' reply to shutdown notice '''
        self.node.shutdown_host(request.host, 
            signature=request.signature, 
            key=request.key,
            nonce=request.nonce)

    ###########################################
    # Protocol Command Senders
    ###########################################
    def send_store(self, host, key, val):
        ''' send key/val, might respond with host '''
        return self.send_message(host, 'store', key=key, val=val)

    def send_find(self, host, key):
        ''' find key - they respond with host or key '''
        return self.send_message(host,'find', key=key)

    def send_host(self, host, rhost):
        ''' send host, no response '''
        return self.send_message(host, 'store_host', pubkey=rhost.pubkey, 
            address=rhost.address, port=rhost.udp_port, signature=host.signature)

    def send_ping(self, host):
        ''' ping host, they respond with a store_host '''
        return self.send_message(host, 'ping')
    
    def send_shutdown_notify(self, host, node_id, nonce, signature):
        ''' notify host we are shutting down '''
        return self.send_message(host, 
            'shutdown_notify',
            signature = signature,
            nonce = nonce,
            key = node_id
        )

    def send_message(self, host, **kwargs):
        msg = DatagramParser.encode(**kwargs)
        try:
            self.transport.write(msg, (host.address, host.udp_port))
        except socket_error as serr:
            # is the muticast unreachable?
            if serr.errno != errno.ENETUNREACH:
                # Not the error we are looking for, re-raise
                raise serr
            return True
        return False

    ###########################################
    # Server Utility Functions
    ###########################################
    def broadcast_loop(self):
        ''' announce presence on lan '''
        interval = 0.5
        # Send multicast announce message
        err = self.send_message(self.broadcast_msg, (self.multicast_group, self.broadcast_port))
        if err:
            # make sure we refresh our address info
            self.host.address = None
            print 'Network unreachable'
            interval = 5
        if self.broadcast == True:
            app.reactor.callLater(interval, self.broadcast_loop)

    def assign_attrs(self, **kwargs):
        ''' Assign Attributes to self '''
        for k, v in kwargs.iteritems():
            if hasattr(self, k):
                setattr( self, k, v)
            else:
                raise AttributeError('Unknown attribute: %s' % k)

    @property
    def addr_port(self):
        return (self.address, self.listen_port,)
 
    def startProtocol(self):
        # Join a specific multicast group, which is the IP we will respond to
        self.transport.joinGroup(self.multicast_group)
        self.check_address()
    def shutdown(self):
        self.node.shutdown()

    def check_address(self):
        # get our ip addr for filtering msgs from self
        if not self.address:
            self.address = get_address()
        # auth signs, protocol picks format
        #signature, nonce = self.node.sign( self.address, self.listen_port)
        #self.broadcast_msg = DatagramParser.encode(
        #    'store_host',
        #    address=self.address,
        #    udp_port=self.listen_port,
        #    signature=signature,
        #    nonce=nonce
        #)

from hashlib import sha256

def khash(key):
    return sha256(key).digest()

###########################################
# Distributed Hash Table Node
###########################################

from twisted.internet.task import LoopingCall

class DHTNode(object):
    '''
    - decouple dht from network code
    - has function to store host, key/val
    - auto adjust bucket size
    '''
    MIN_SIZE = 2**32        # Minimum node size 
    timeout = 15*60*1000    # mark host as stale when updated_at greater than
    bits=256                # bit size of key space
    k = 2**bits             # max int
    ubound = k              # max distance from node id

    def __init__(self, protocol, **kwargs):
        self.protocol = protocol
        # Generate ephemeral key
        self.auth = Authorization(**kwargs)

        # config resources
        self._hosts_lock = Lock()
        self._hosts = [None for k in range(self.bits)] # array to hold hosts
        self._key_vals_lock = Lock()
        self._key_vals = {}

        # kick off loop
        self.refresh_loop = LoopingCall( self.__hosts_refresh__ )
        self.refresh_loop.start(60)

    def sign(self, *args):
        ''' sign message '''
        msg = [str(arg) for arg in args]
        nonce = self.auth.time_now()
        msg.append(str(nonce))
        msg = ':'.join(msg)
        signature = self.auth.sign(msg)
        return [signature, nonce]

    def distance(self, a, b):
        ''' calculate distance between 2 nodes '''
        if a == b: return 0
        if a < b: return b-a
        return self.k + (b-a)
    
    def within_range(self, key):
        ''' is the key within range of our node '''
        return self.ubound > self.distance( self.node_id, key)

    def update_ubound(self):
        ''' update ubound '''
        # hosts already locked
        hosts = [h for h in self._hosts if h]
        # split node
        if len(hosts) > 19:
            dist = self.distance(self.node_id, hosts[9].node_id)
            # cant be smaller than min size
            if dist < self.MIN_SIZE:
                dist = self.MIN_SIZE
            self.ubound = dist
        else:
            self.ubound = self.k
    
    def host_info(self, node_id):
        ''' calculate dist/pos of Node'''
        # Calculate distance and index position
        dist = self.distance( self.host.node_id, node_id)
        pos = round(log(dist, 2)) % self.bits
        return [dist, pos]

    # 
    # resources called by protocol
    #
    def store(self, host, key, val):
        ''' Store a key/val pair '''
        added = False
        if not self.within_range(key):
            for h in self.find_nearest_hosts(key):
                self.protocol.send_host( host, h )
            return False
        self._key_vals_lock.acquire()
        if key not in self._key_vals.keys():
            self._key_vals[key] = []
        if val not in key_vals[key]:
            self._key_vals[key].append(val)
        self._key_vals_lock.release()
        return True
    
    def find(self, host, key):
        ''' find key '''
        self._key_vals_lock.acquire()
        if key in self._key_vals.keys():
            # send vals
            for val in self._key_vals[key]:
                self.protocol.send_key( host, key, val)
        else:
            # see if there are any better hosts
            for h in self.find_nearest_hosts(key):
                self.protocol.send_host( host, h )
        self._key_vals_lock.release()
    
    def store_host(self, host, rhost ):
        ''' store host if the information is valid  '''
        d = rhost.isValid()
        d.addCallback( rhost.pubkey, pubkey=pubkey)
        d.addCallback( rhost.pubkey.isValid)
        d.addCallback( self.__store_host__, host, rhost)

    def __store_host__(self, host, rhost, force=False):
        ''' add/refresh host '''
        # Calculate distance and index position
        dist, pos = self.host_info(rhost)
        # Acquire Lock
        self._hosts_lock.acquire()
        old = self._hosts[pos]
        # Add host if none exists
        if not old:
            self._hosts[pos] = rhost
        # update host
        elif old.node_id == rhost.node_id:
            old.last_seen_at = old.time_now()
        # replace stale node
        elif old.is_stale or force:
            self._hosts[pos] = rhost
        else:
            # we already have a node for this spot, pass
            # Release Lock
            self._hosts_lock.release()
            return False
        self.update_ubound()
        # Release Lock
        self._hosts_lock.release()
        return True

    def find_host(self, node_id):
        ''' Find a host matching the key '''
        dist, pos = host_info(node_id)
        self._hosts_lock.acquire()
        host = self._hosts[pos]
        self._hosts_lock.release()
        if host and host.node_id == node_id:
            return host
        return None

    def remove_host(self, node_id):
        ''' remove host if it has a matching node_id'''
        removed = False
        dist, pos = host_info(node_id)
        self._hosts_lock.acquire()
        host = self._hosts[pos]
        if host and host.node_id == node_id:
            self._hosts[pos] = None
            removed = True
        self._hosts_lock.release()
        return removed 

    def shutdown_host(self, host, signature, key, nonce):
        node_id = host.node_id
        # Calculate distance and index position
        dist, pos = self.host_info(host)
        rhost = None

        self._hosts_lock.acquire()
        # verify message 
        rhost = self._hosts[pos]
        if not rhost: return
        if rhost.node_id != host.node_id: return
        if not rhost.verify(signature, message): return
        self.protocol.send_find( rhost, self.node_id)
        self._hosts[pos] = None
        self._hosts_lock.release()

    def __hosts_refresh__(self):
        ''' 
        ping hosts so they don't go stale
        remove stale hosts
        '''
        self._hosts_lock.acquire()
        # clean up list and ping
        for i, host in enumerate(self._hosts): 
            if not(host):
                continue
            if host.is_stale:
                # remove from list
                self._hosts[i] = None
                continue
            self.protocol.send_ping(host)
        self._hosts_lock.release()

    # Not called by remote 
    def find_nearest_hosts(self, key, n=3, lock=True):
        ''' return hosts near key ''' 
        result = []
        # Calculate distance and index position
        dist, pos = self.host_info(key)
        # Acquire Lock 
        if lock:
            self._hosts_lock.acquire()        
        # Get 3 closest hosts to node_id
        for b in range(0, self.bits):
            i = (pos-b) % self.bits
            if self._hosts[i]: 
                result.append( self._hosts[i] )
            if len(result) >= n: 
                break
        if lock:
            # release lock   
            self._hosts_lock.release()
        return result

    def host_count(self):
        ''' count hosts '''
        count = 0
        self._hosts_lock.acquire()        
        for h in self._hosts:
            if h:
                count += 1
        # release lock   
        self._hosts_lock.release()
        return count 
    
    def shutdown(self):
        ''' save hosts and exit '''
        if self.refresh_loop.running:
            self.refresh_loop.stop()
        self.__send_shutdown_notices__()

    def __send_shutdown_notices__(self):
        self._hosts_lock.acquire()
        nonce = self.auth.time_now()
        signature = self.auth.sign( 'shutdown:%s:%s' % (self.auth.pubkey_str, nonce) )
        for host in self._hosts:
            if not host: 
                continue   
            host.save()
            # notify this host that we are shutting down
            self.protocol.send_shutdown_notify(
                host,
                nonce=nonce,
                signature=signature,
                key=self.host.node_id)        
        # release lock   
        self._hosts_lock.release()        
