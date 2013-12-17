# Simple UDP Multicast Server example
# Kyle Robertson
# A Few Screws Loose, LLC
# http://www.afslgames.com
# ra1n@gmx.net
# MulticastServer.py

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.application.internet import MulticastServer

from threading import Lock
from rainmaker_app import app
from rainmaker_app.model.pubkey import Pubkey
import re

############################################
# Utility Functions
############################################

def decr_ttl(ttl):
    ttl = int(ttl)
    ttl -= 1
    if ttl >= MAX_TTL:
        ttl = MAX_TTL - 1
    elif ttl < 0:
        ttl = 0
    return ttl
    
############################################
# Module Level Instance Variables
############################################
app_key = 'rain:%s' % (app.version)
self_key = 'rain:%s:%s' % (app.version, app.guid)
broadcast_msg = '%s:set_host' % (self_key)
MAX_TTL = 7
_hosts_lock = Lock()
_hosts = {}
_key_vals_lock = Lock()
_key_vals = {}

###########################################
# Locking operations 
###########################################
def add_keyval(key, val):
    added = False
    _key_vals_lock.aquire()
    if key not in _key_vals.keys():
        _key_vals[key] = []
    if val not in key_vals[key]:
        added = True
        _key_vals[key].append(val)
    _key_vals_lock.release()
    return added

from copy import deepcopy
def get_vals(key):
    _key_vals_lock.aquire()
    if key in _key_vals.keys():
        result = deepcopy( _key_vals[key] )
    _key_vals_lock.release()
    return result

def add_host(address, port, guid):
    _hosts_lock.aquire()
    added = False
    addr_port = [str(address), int(port)]
    if guid not in _hosts.keys():
        _hosts[guid] = []
    if addr_port not in _hosts[guid]:
        added = True
        _hosts[guid].append(addr_port)
    _hosts_lock.release()
    return added

def get_host(guid):
    _hosts_lock.aquire()
    if guid in _hosts.keys():
        result = deepcopy( _hosts[guid] )
    _hosts_lock.release()
    return result

def get_hosts(limit, but_not):
    _hosts_lock.aquire()
    result = [] 
    for k, v in hosts.iteritems():
        for addr_port in v:
            result += [ addr_port for addr_port in hosts if addr_port not in but_not]
        if limit and len(result) > limit:
            result = result[0:limit]
            break
    hosts_lock.release()
    return result
    
###########################################
# Server 
###########################################
import errno
from socket import error as socket_error
from .net_utils import is_compatible

class MulticastServerUDP(DatagramProtocol):
    
    multicast_group = '224.0.0.0'
    listen_port = 8500    
    broadcast = True
    broadcast_port = 8500

    def __init__(self, **kwargs):
        # responders
        self.routes = {    
            'store': [ self.store_command, 3],
            'find': [ self.find_command, 1],
            'set_host': [ self.set_host_command, 1],
            'get_host': [ self.get_host_command, 0],
            'announce': [ self.announce_command, 0]
        }

        for k, v in kwargs.iteritems():
            if hasattr(self, k):
                setattr( self, k, v)
            else:
                raise AttributeError('Unknown attribute: %s' % k)
    
    def startProtocol(self):
        print 'Joining multicast group %s' % self.multicast_group
        # Join a specific multicast group, which is the IP we will respond to
        self.transport.joinGroup(self.multicast_group)

    def datagramReceived(self, datagram, address):
        # The uniqueID check is to ensure we only service requests from ourselves
        if udp_filter( datagram ):
            return
        address, port = address
        self.process_datagram( address, port, datagram)

    def broadcast_loop(self):
        ''' announce presence on lan '''
        request = '%s,announce' % app_key
        interval = 0.5
        try:
            # Send multicast announce message
            self.transport.write(self_key, (self.multicast_group, self.broadcast_port))
        except socket_error as serr:
            # is the muticast unreachable?
            if serr.errno != errno.ENETUNREACH:
                # Not the error we are looking for, re-raise
                raise serr
            print 'Network unreachable'
            interval = 5

        if self.broadcast == True:
            app.reactor.callLater(interval, self.broadcast_loop)
    
    ###############################################
    # UDP Commands
    ###############################################
    def store_command(address, port, ver, guid, ttl, key, val):
        ''' Store a match '''
        ttl = decr_ttl(ttl)
        added = add_keyval(key, val)
        if not(added) or ttl == 0: return
        message = ':'.join([ self_key, 'find', str(ttl), key, val] )
        broadcast( message, not_to=(address, port))
            
    def find_command(address, port, ver, guid, ttl, key):
        ''' Check to see if we have any matches '''
        ttl = decr_ttl(ttl)
    
        # broadcast message 
        message = ':'.join([ self_key, 'find', str(ttl), key] )
        broadcast( message, ttl, not_to=(address, port))
        
        # search for match
        vals = get_vals(key)
        if not vals: return
        
        # return finds
        for val in vals:
            message = ':'.join([ self_key, 'store', str(ttl), key, val] )
            self.transport.write(message, (address, port))
        
    def set_host_command(address, port, ver, guid, r_guid, r_address, r_port):
        ''' add host info '''
        added = set_host( r_address, r_port, r_guid)
    
    def get_host_command(address, port, ver, guid, r_guid):
        ''' get all hosts with this guid '''
        hosts = get_host( r_guid )
        for h in hosts:
            r_address, r_port = h
            message = ':'.join([self_key, r_address, r_port])
            self.transport.write(message, (address, port))

    def announce_command(address, port, ver, guid):
        ''' add host info '''
        added = set_host( address, port, guid)

    ###########################################
    # Server Utility Functions
    ###########################################
    def process_datagram(self, address, port, datagram ):
        ''' split datagram into parameters '''
        try:
            data = datagram.split(':')
            ver, host, action = data[1:3]
            args = data[4:]
            if not is_compatible(ver):
                print 'Incompatible Version: %s' % ver
                return
            if not action in self.routes.keys():
                print 'Unknown action: %s' % action
                return
            func, nargs = self.routes[action]
            if nargs != len(data) - 5:
                print 'narg mismatch'
                return
            func(address, port, ver, *data[5:])
        except:
            print 'Datagram Error'
            return None

    def broadcast( message, ttl, not_to=None):
        if not not_to:
            not_to = []
        hosts = get_hosts(0, not_to)
        if ttl == 0: return
        for h in hosts:
            address, port = h
            self.transport.write(message, (address, port))
    
    def load_pubkeys(self, pubkeys):
        pass

def udp_filter( datagram ):
    ''' block data from self '''
    if datagram.startswith( self_key ):
        return True
    if datagram.startswith( app_key ):
        return False
    return True
