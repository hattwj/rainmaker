from hashlib import sha256
def khash(key):
    return sha256(key).digest()

###########################################
# Distributed Hash Table Node
###########################################
from threading import Lock
from math import log
import re

from twisted.internet import defer
from twisted.internet.task import LoopingCall
from rainmaker_app import app
from rainmaker_app.db.models import Host, Authorization

class DHTNode(object):
    '''
    - decouple dht from network code
    - has function to store host, key/val
    - auto adjust bucket size

    - hosts hold key/vals for specific range of keys
    - keys are pubkey addr_info pairs
    - hosts are key/vals too, just a finger table

    TLS:
    - shared pkey used to authorize ephemeral key
    '''
    MIN_SIZE = 2**32        # Minimum node size 
    timeout = 15*60*1000    # mark host as stale when updated_at greater than
    bits=256                # bit size of key space
    k = 2**bits             # max int
    ubound = k              # max distance from node id

    def __init__(self, **kwargs):
        # Generate ephemeral key
        self.auth = app.auth

        # config resources
        self._hosts_lock = Lock()
        self._hosts = [None for k in range(self.bits)] # array to hold hosts
        self._key_vals_lock = Lock()
        self._key_vals = {}

        # kick off loop
        self.refresh_loop = LoopingCall( self.__hosts_refresh__ )
        self.refresh_loop.start(60)
    
    @defer.inlineCallbacks
    def start(self):
        # contact hosts 
        hosts = yield Host.all()
        for host in hosts:
            app.client.send_ping( host )

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
                app.client.send_host( host, h )
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
                app.client.send_key( host, key, val)
        else:
            # see if there are any better hosts
            for h in self.find_nearest_hosts(key):
                app.client.send_host( host, h )
        self._key_vals_lock.release()
    
    def store_host(self, host, rhost ):
        ''' store host if the information is valid  '''
        return rhost.isValid().addCallback( self.__store_host__, host, rhost)

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
        ''' '''
        # Calculate distance and index position
        dist, pos = self.host_info(host)
        rhost = None
        # 
        self._hosts_lock.acquire()
        # verify message 
        rhost = self._hosts[pos]
        if not rhost: return
        if rhost.node_id != host.node_id: return
        if not rhost.verify(signature, message): return
        app.client.send_find( rhost, self.node_id)
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
            app.client.send_ping(host)
        self._hosts_lock.release()
    
    def refresh_host(self, host):
        ''' refresh contact with host '''
        host.isValid().addCallback( app.client.send_ping, host)
        
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
            app.client.send_shutdown_notify(
                host,
                nonce=nonce,
                signature=signature,
                key=self.host.node_id)        
        # release lock   
        self._hosts_lock.release()

'''
Ephemeral Auth Purpose:
- signed by shared pkey pubkeys during TLS start

DHT Plan:
- node_id is hash of addr_info
- store: pubkey hash / host info
- rework finger table for address resets
'''

