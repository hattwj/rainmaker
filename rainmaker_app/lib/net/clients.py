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
from rainmaker_app.model.host import Host
log = logger.create(__name__)

from rainmaker_app import app

class ClientProtocol(ServerProtocol):

    def __init__(self, factory, host):
        self.factory = factory
        self.host = host
    
    def connectionMade(self):
        ''' '''
        self.connected = True
        peer = self.transport.getPeer()
        self.peer_addr_port = (peer.host, peer.port,)
        d = self.version_check()
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
        d.addCallbacks(self.setup_hosts, self.startup_failed)
        d.addCallbacks(self.start_tls, self.startup_failed)
        d.addCallbacks(self.verify_tls, self.startup_failed)
        d.addCallbacks(self.authenticate, self.startup_failed)
        d.addCallbacks(self.sync, self.startup_failed)
    @defer.inlineCallbacks 
    def setup_hosts(self, result):
        '''
            swap host information with server            
        '''
        log.msg('Client: sending host info')
        kwargs = app.tcp_server.host.to_dict(host_param_keys)
        d = self.callRemote(SetGetHostCommand, **kwargs)
        d.addErrback(self.startup_failed)
        kwargs = yield d
        self.session.host = yield Host.findOrCreate(**kwargs)
        #defer.returnValue(True)

    @defer.inlineCallbacks
    def start_tls(self, result):
        '''
            request TLS from server
        '''
        log.msg('Client: Requesting TLS')
        result = yield self.callRemote(amp.StartTLS, **self.session.certParams())
        log.msg(result)
        #defer.returnValue(True)
    
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
        #defer.returnValue(True)
    @defer.inlineCallbacks
    def authenticate(self, result):
        '''
            negotiate login details with server
        '''
        result = yield self.callRemote(AuthCommand, **self.session.authorizeParams())
        self.session.authorize(**result)
        log.msg('We have authenticated!')
        #defer.returnValue(True)
    @defer.inlineCallbacks
    def sync(self, result):
        '''
        '''
        # Exchange sync path details#
        sync_path = self.session.sync_path
        log.msg('Client: syncing  %s' % sync_path.root)
        keys = GetSyncPathCommand.arguments_keys()
        data = sync_path.to_dict(keys)
        log.msg(data)
        result = yield self.callRemote(GetSyncPathCommand, **data)
        log.msg(result)
        # get diffs from server
        # send diffs to server
        
class ClientFactory(protocol.ClientFactory):
    '''
        class methods provide constructors for various client actions
        - client protocol classes each provide pre-programmed functionality
    '''
    def __init__(self, addr_port, protocol, **kwargs):
        self.kwargs = kwargs
        addr, port = addr_port
        self.protocol = protocol
        app.reactor.connectTCP(addr, port, self)

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

