from os import urandom

from threading import Lock
from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log

from .net_utils import is_compatible, require_secure
from .exceptions import *
from .commands import *
from .start_tls import ServerProtocol
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app import app


class ClientProtocol(ServerProtocol):

    def __init__(self, factory):
        self.factory = factory
    
    def connectionMade(self):
        ''' '''
        self.connected = True
        peer = self.transport.getPeer()
        self.peer_addr_port = (peer.host, peer.port,)
        d = self.version_check()
        #d.addErrback(self.startup_failed)
        self.connecting(d)        

    def connecting(self, d):
        raise AttributeError('Abstract method')

    @defer.inlineCallbacks
    def version_check(self, *params):
        result = yield self.callRemote( VersionCheckCommand, version = app.version)
        if not is_compatible(result['version']):
            raise StartTLSFailed('Incompatible Version: %s' % result['version'])

    def startup_failed(self, reason):
        log.msg('client: start_tls_failed')
        log.msg(reason.getTraceback())
        reason.trap(StartTLSFailed)
        reason.trap(AuthRequired)
        self.transport.loseConnection()

class ClientPingProtocol(ClientProtocol):
    
    def connecting(self, d):
        ''' '''
        print 66
        d.addCallbacks(self.ping, self.startup_failed)
   
    @defer.inlineCallbacks
    def ping(self, *params):
        result = yield self.callRemote(PingCommand)
        log.msg(result)
        self.transport.loseConnection()

class ClientHandshakeProtocol(ClientProtocol):

    def connecting(self, d):
        print 66
        d.addCallbacks(self.get_pubkeys, self.startup_failed)
        
    @defer.inlineCallbacks
    def get_pubkeys(self):
        result = yield self.callRemote(GetPubkeysCommand)
        pubkeys = result['pubkeys']
        if len(pubkeys) == 0:
            return
        auths = yield Authorization(where=['pubkey_str IN (?)', pubkeys], limit=1)
        for auth in auths:
            ClientFactory.sync(self.peer_addr_port, auth)

class ClientSyncProtocol(ServerProtocol):

    def __init__(self, factory, auth):
        self.factory = factory
        self.auth = auth
    
    def __connecting(self, d):
        ''' '''
        d.addCallbacks(self.set_pubkey, self.startup_failed)
        d.addCallbacks(self.start_tls, self.startup_failed)
        d.addCallbacks(self.authenticate, self.startup_failed)

    @defer.inlineCallbacks
    def version_check(self):
        result = yield self.callRemote( VersionCheckCommand, version = app.version)
        if not is_compatible(result['version']):
            raise StartTLSFailed('Incompatible Version: %s' % result['version'])
        self.factory.connectionMade(self)

    @defer.inlineCallbacks
    def set_pubkey(self): 
        kwargs ={'guid':self.auth.guid}
        result = yield self.callRemote(SetPubkeyCommand, **kwargs)
        log.msg(result)

    @defer.inlineCallbacks
    def start_tls(self):
        '''
            request TLS from server
        '''
        result = yield self.callRemote(amp.StartTLS, **self.auth.certParams())
        log.msg(result)
     
class ClientFactory(protocol.ClientFactory):
    '''
        class methods provide constructors for various client actions
        - client protocol classes each provide pre-programmed functionality
    '''

    def __init__(self, addr_port, protocol, **kwargs):
        self.kwargs = kwargs
        self.addr, self.port = addr_port
        self.protocol = protocol
        app.reactor.connectTCP(self.addr, self.port, self)

    def buildProtocol(self, addr):
        return self.protocol(self, **self.kwargs)
    
    def clientConnectionFailed(self, client, reason):
        log.msg( "connection failed: %s" % reason.getErrorMessage() )

    def clientConnectionLost(self, client, reason):
        log.msg("connection lost: %s" % reason.getErrorMessage() )
   
    def commandFailed(self, *args):
        log.msg('Command failed')
        log.msg(args)

    def connectionMade(self, client):
        ''' A client made connection '''
        log.msg("Connection made: ")

    @classmethod
    def config(klass, **kwargs):
        '''
            configure klass
        '''
        assign_attrs(klass, **kwargs)

    @classmethod
    def ping(klass, addr_port):
        '''
            ping  remote server
        '''
        klass(addr_port, ClientPingProtocol)

    @classmethod
    def sync(klass, addr_port, auth):
        '''
            securely connect and sync with remote server
        '''
        klass(addr_port, ClientSyncProtocol, auth=auth)

