from os import urandom

from threading import Lock
from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
#from twisted.python import log

from .net_utils import is_compatible
from .exceptions import *
from .commands import *
from .start_tls import ServerProtocol
from .session import Session, require_secure
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app.lib import logger
log = logger.create(__name__)

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

class ClientSyncProtocol(ClientProtocol):

    def __init__(self, factory, auth, sync_path):
        self.factory = factory
        self.auth = auth
        self.sync_path = sync_path
    
    def connecting(self, d):
        '''
            Parent commands have run and now we get to act
        '''
        self.session = Session(app.auth)
        self.session.sync_path = self.sync_path
        d.addCallbacks(self.set_pubkey, self.startup_failed)
        d.addCallbacks(self.start_tls, self.startup_failed)
        d.addCallbacks(self.verify_tls, self.startup_failed)
        d.addCallbacks(self.authenticate, self.startup_failed)

    @defer.inlineCallbacks
    def set_pubkey(self, result): 
        '''
            Set the certificate string for this connection
        '''
        log.msg('Client: Setting pubkey')
        kwargs ={'cert':self.auth.cert_str}
        result = yield self.callRemote(SetPubkeyCommand, **kwargs)
        print 'Here is the client result from set pubkey:'
        print result
        self.session.peer_cert = result['cert']
        defer.returnValue(True)

    @defer.inlineCallbacks
    def start_tls(self, result):
        '''
            request TLS from server
        '''
        log.msg('Client: Requesting TLS')
        result = yield self.callRemote(amp.StartTLS, **self.session.certParams())
        log.msg(result)
        defer.returnValue(True)
    
    @amp.StartTLS.responder
    def startTLS_responder(self):
        log.msg( "Client: We are starting TLS" )
        return self.session.certParams()

    @defer.inlineCallbacks 
    def verify_tls(self, result):
        '''
            verify that we are connected securely
        '''
        result = yield self.callRemote(SecurePingCommand)
        self.connection_secure()
        log.msg('Client: We are connected securely')

    @defer.inlineCallbacks
    def authenticate(self, result):
        '''
            negotiate login details with server
        '''
        result = yield self.callRemote(AuthCommand, **self.session.authorizeParams())
        print result
        print 'We have authenticated!'

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
    def sync(klass, addr_port, auth, sync_path):
        '''
            securely connect and sync with remote server
        '''
        klass(addr_port, ClientSyncProtocol, auth=auth, sync_path=sync_path)

