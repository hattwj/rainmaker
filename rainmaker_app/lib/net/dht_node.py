from hashlib import sha256
def khash(key):
    return sha256(key).digest()

###########################################
# Distributed Hash Table Node
###########################################
from threading import Lock
import math
import re

from twisted.python import log
from twisted.internet import defer
from twisted.internet.task import LoopingCall

from rainmaker_app import app
from rainmaker_app.db.models import Host, Authorization

class DHTNode(object):
    '''
    About:
    - has function to store host, key/val
    - auto adjust bucket size
    
    Keys:
    - hosts hold key/vals for specific range of keys
    - keys are pubkey addr_info pairs

    Hosts:
    - hosts are key/vals too, just a finger table

    Periodically:
    - Scan Host table and send a ping
    -- Returned pings we try to add to finger table
    -- Stale hosts are deleted from database

    - Scan Authorizations Table:
    -- Get nearest nodes
    -- Store Key
    -- Find Key
    --- Initialize Sync

    - Look to fill out finger table:
    -- 
    '''
    L_HOSTS_LOAD    =  120  # Loop: 
    L_HOSTS_REFRESH =  150  # Loop: refresh connections every x seconds
    L_HOSTS_FIND    =  30   # Loop:
    L_AUTHS_FIND    =  30   # Loop:

    MIN_SIZE = 2**32        # Minimum node size
    MIN_HOST_AGE = 300*1000 # Min msec to wait between pings
    
    MIN_CONNECTIONS = 8     # Min number of connections
    MAX_CONNECTIONS = 32    # Max number of connections

    bits=256                # bit size of key space
    k = 2**bits             # max int
    ubound = k              # max distance from node id

    def __init__(self, auth):
        # Generate ephemeral key
        self.auth = auth
        self.node_id = self.auth.pubkey.guid

        # config resources
        self._hosts_lock = Lock()
        self._hosts = [None for k in range(self.bits)] # array to hold hosts
        self._key_vals_lock = Lock()
        self._key_vals = {}
  
    @defer.inlineCallbacks
    def start(self):
        ''' 
        Run DHT Node
        '''
        yield self.__hosts_load__()
        self.__hosts_find__()
        self.__auths_find__()
        app.reactor.callLater(self.L_HOSTS_REFRESH, self.__hosts_refresh__)
        
    #
    # DHT Loops
    #
    def __hosts_refresh__(self):
        ''' 
        ping hosts so they don't go stale
        remove stale hosts
        '''
        log.msg('Refreshing host information')
        self._hosts_lock.acquire()
        # clean up list and ping
        for i, host in enumerate(self._hosts): 
            if not(host):
                continue
            if host.is_stale:
                # remove from list
                self._hosts[i] = None
                host.delete()
                continue
            app.client.send_ping(host)
        self._hosts_lock.release()
        app.reactor.callLater(self.L_HOSTS_REFRESH, self.__hosts_refresh__)

    def __hosts_find__(self):
        '''
        Search through nodes array for empty elements and attempt to find 
        nodes that can fill that sp
        '''
        # Don't look for hosts if were above min 
        if self.host_count >= self.MIN_CONNECTIONS:
            app.reactor.callLater(self.L_HOSTS_FIND, self.__hosts_find__)
            return

        # bin count depends on number of of known hosts
        bin_count = self.host_count
        bin_size = len(self._hosts) // bin_count
        # bins to check for missing nodes
        bins = [None for j in range(0, bin_count)]

        self._hosts_lock.acquire()
        # require 1 in x buckets full
        for idx, host in enumerate(self._hosts):
            cur_bin = idx // bin_size
            if bins[cur_bin]:
                # already finding / have host
                continue
            if host:
                # already have host
                bins[cur_bin] = True
                continue
            # mark as searching
            bins[cur_bin] = True
            # find host for bucket
            node_id = self.bucket_to_node_id(idx)
            hosts = self.find_nearest_hosts(node_id)
            for host in hosts:
                send.client.send_find_host(node_id)
        self._hosts_lock.release()
        app.reactor.callLater(self.L_HOSTS_FIND, self.__hosts_find__)

    @defer.inlineCallbacks
    def __hosts_load__(self):
        ''' Scan through host table and try to fill out nodes array '''
        hosts = yield Host.all()
        for host in hosts:
            self.store_host(host)
        app.reactor.callLater(self.L_HOSTS_LOAD, self.__hosts_load__)

    @defer.inlineCallbacks
    def __auths_find__(self):
        ''' Search auths table, find auths '''
        auths = yield Authorization.all()
        for auth in auths:
            hosts = self.find_nearest_hosts(auth.node_id)
            for host in hosts:
                self.client.send_find_key(host, auth.node_id)
                self.client.send_store_key(host, auth.encrypted_export() )
        app.reactor.callLater(self.L_AUTHS_FIND, self.__auths_find__)
    
    #
    # END of Loops
    #
    
    def sign(self, *args):
        ''' sign message '''
        msg = [str(arg) for arg in args]
        signed_at = self.auth.time_now()
        msg.append(str(signed_at))
        msg = ':'.join(msg)
        signature = self.auth.sign(msg)
        return [signature, signed_at]

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
        dist = self.distance( self.node_id, node_id)
        pos = int(round(math.log(dist, 2)) % self.bits)
        return [dist, pos]

    def pos_to_node_id(self, pos):
        ''' convert bucket pos to node_id '''
        return (2**pos + self.node_id) % self.k

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
    
    def store_host(self, rhost ):
        ''' store host if the information is valid  '''
        if not rhost.verify_sig():
            log.msg('Refusing to store host with invalid signature')
            return False
        return self.__store_host__(rhost)

    def __store_host__(self, rhost, force=False):
        ''' add/refresh host '''
        # Calculate distance and index position
        dist, pos = self.host_info(rhost.node_id)
        # Acquire Lock
        self._hosts_lock.acquire()
        old = self._hosts[pos]
        # Add host if none exists
        if not old:
            self._hosts[pos] = rhost
            app.client
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

    def shutdown_host(self, host, signature, key, signed_at):
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
     
    # Not called by remote 
    def find_nearest_hosts(self, node_id, n=3, lock=True):
        ''' return hosts near node_id ''' 
        result = []
        # Calculate distance and index position
        dist, pos = self.host_info(node_id)
        # Acquire Lock 
        if lock:
            self._hosts_lock.acquire()        
        # Get n closest hosts to node_id
        for b in range(0, self.bits):
            # get index of possible host
            i = (pos-b) % self.bits
            if self._hosts[i]:
                # add result
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
