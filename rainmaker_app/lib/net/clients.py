from threading import Lock
from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log


from .net_utils import is_compatible, require_secure
from .exceptions import *
from .commands import *
from .start_tls import ServerProtocol
from rainmaker_app.lib.util import DeferredDict
from rainmaker_app import app

class ClientProtocol(ServerProtocol):
    server_version = None
    connected = False
    peer_addr_port = None

    def __init__(self, factory, **kwargs):
        self.factory = factory
        self.commands = defer.DeferredQueue()
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def connectionMade(self):
        ''' '''
        self.connected = True
        peer = self.transport.getPeer()
        self.peer_addr_port = (peer.host, peer.port,)
        d = self.version_check()
        d.addErrback(self.startup_failed)
        d.addCallback(self.finish_connecting)
    
    def finish_connecting(self, *args):
        self.factory.connectionMade(self)
        self.run_commands()
   
    @defer.inlineCallbacks
    def run_commands(self, *args):
        ''' run all commands '''
        while self.connected:
            cmd, args, kwargs = yield self.commands.get()
            if args and kwargs:
                d = cmd(*args, **kwargs)
            elif args:
                d = cmd(*args)
            elif kwargs:
                d= cmd(**kwargs)
            else:
                d = cmd()
            d.addErrback(self.command_error)

    def command_error(self, reason):
        ''' An error occurred while running a server command '''
        log.msg(reason.getTraceback()) 

    @defer.inlineCallbacks
    def version_check(self):
        result = yield self.callRemote( VersionCheckCommand, version = app.version)
        if not is_compatible(result['version']):
            raise StartTLSFailed('Incompatible Version: %s' % result['version'])
        log.msg(result)

    def startup_failed(self, reason):
        log.msg('client: start_tls_failed')
        log.msg(reason.getTraceback())
        reason.trap(StartTLSFailed)
        reason.trap(AuthRequired)
        self.transport.loseConnection()

class ClientSecureProtocol(ClientProtocol):
    server_version = None
    authorization = None
    certParams = None

    @defer.inlineCallbacks
    def set_pubkey(self, *chain):
        ''' set_pubkey on server '''
        result = yield self.callRemote( SetPubkeyCommand, guid=self.authorization.guid)
        if result['response_code'] != 200:
            log.msg(result)
            raise StartTLSFailed('Unknown Certificate')

    @defer.inlineCallbacks
    def start_tls(self, *chain):
        result = yield self.callRemote( amp.StartTLS, **self.authorization.certParams() )
        log.msg(result)

    def startup_failed(self, reason):
        log.msg('client: start_tls_failed')
        log.msg(reason.getTraceback())
        reason.trap(StartTLSFailed)
        reason.trap(AuthRequired)
        self.transport.loseConnection()

class ClientFactory(protocol.ClientFactory):
    ''' track clients? '''

    def __init__(self, **kwargs):
        self.clients = DeferredDict()
        if not kwargs: 
            kwargs = {}
        self.kwargs = kwargs

    def buildProtocol(self, addr):
        return ClientProtocol( self )
    
    def clientConnectionFailed(self, client, reason):
        log.msg( "connection failed: %s" % reason.getErrorMessage() )

    def clientConnectionLost(self, client, reason):
        log.msg("connection lost: %s" % reason.getErrorMessage())
   
    def commandFailed(self, *args):
        log.msg('Command failed')
        log.msg(args)

    def connectionMade(self, client):
        ''' A client made connection '''
        addr_port = client.peer_addr_port
        log.msg("Connection made: ")
        log.msg(addr_port)
        if addr_port in self.clients.keys():
            self.clients[addr_port].transport.loseConnection() 
        self.clients[addr_port] = client
    
    def get_client(self, addr_port):
        ''' get a client '''
        if not addr_port in self.clients.keys():
            addr, port = addr_port
            app.reactor.connectTCP(addr, port, self)
        return self.clients[addr_port]
    
    @defer.inlineCallbacks
    def send_ping(self, host):
        valid = yield host.isValid()
        if not valid:
            return
        client = yield self.get_client(host.addr_port)
        if not client: 
            return
        client.callRemote(PingHostCommand).addErrback(self.commandFailed)
