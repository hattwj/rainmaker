from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log

import rainmaker_app
from rainmaker_app import app
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app.lib.net import connections
from rainmaker_app.lib.net.resources import files_resource, messages_resource 
from rainmaker_app.db.models import *

from .net_utils import is_compatible, require_secure, get_address, \
    report_errors
from .exceptions import *
from .commands import *

class Session(object):

    def __init__(self, auth):
        self.auth = auth
        self.rand = urandom(500)
        self._peer_rand = None
        self._peer_pass = None
        self._peer_cert = None
    
    @defer.inlineCallbacks
    def check(self, guid):
        auth = 

    @property
    def peer_rand(self):
        return self._peer_rand

    @property.setter
    def peer_rand(self, val):
        '''
            can only be set once
        '''
        if self._peer_rand:
            raise AttributeError('already set')
        self._peer_rand = val
    
    @property
    def peer_sync(self):
        return self._peer_sync

    @property.setter
    def peer_sync(self, val):
        if self._peer_sync:
            raise AttributeError('already set')
        self._peer_sync = val
    
    @property
    def peer_cert(self):
        return self._peer_cert

    @property.setter
    def peer_cert(self, val):
        if self._peer_cert:
            raise AttributeError('already set')
        self._peer_cert = val
    

class ServerProtocol(amp.AMP):
    '''
        c->s: connect
        c->s: check version
        c->s: set_pubkey
        c->s: startTLS
        c->s: set salt
        c->s: authenticate
    '''
    authorization = None     
    sync_path = None    # Set after authentication
    __salt = None       #
    __pepper = None     #

    def __init__(self, factory):
        self.factory = factory
        self.peer_auth = None

    def connectionMade(self):
        log.msg('Connection Made')
        self.addr_port = self.transport.getHost()

        connections.add(self)

    def connectionLost(self, reason):
        log.msg('Connection Lost')
        connections.remove(self)
    
    @FindHostCommand.responder
    def find_host_command(self, **kwargs):
        hosts = app.node.find_nearest_hosts(**kwargs)
        for host in hosts:
            self.callRemote(StoreHostCommand, **host.to_dict() )
        return {'code', 200}

    @StoreHostCommand.responder
    @defer.inlineCallbacks
    def store_host_command(self, **kwargs):
        host = Host(**kwargs)
        d =  host.isValid()
        d.addErrback( self.command_failed )
        valid = yield d
        if valid:
            finger_table.add(host)
        code = 200 if valid else 500
        defer.returnValue( {
            'code': code,
            'errors' : []
        })
    
    @PingCommand.responder
    def ping_command_responder(self):
        log.msg('received ping')
        return {'code':200}
    
    @require_secure
    @SecurePingCommand.responder
    def secure_ping_command_responder(self):
        log.msg('received secure ping')
        return {'code':200}

    @VersionCheckCommand.responder
    def version_check_command_responder(self, version):
        log.msg('client version: %s' % version)
        return {
            'response_code':200,
            'version': app.version
        }

    @SetPubkeyCommand.responder
    def set_pubkey_command_responder(self, cert):
        print 'Recieved cert: ' + cert
        self.peer_cert = cert
        return {'code':200, 'cert': app.auth.cert_str}
    
    @amp.StartTLS.responder
    def startTLS(self):
        log.msg( "server/client: We are starting TLS" )
        return app.auth.certParams(self.peer_cert)
    @require_secure
    @InitAuthCommand.responder
    def init_auth_command_responder(self, rand): 
        return {'rand': urandom(50)}
    @require_secure
    @AuthCommand.responder   
    def auth_command_responder(self, result):
        pass

    @require_secure
    def connection_secure(self):
        log.msg('The connection is now secure')  

    def command_failed(self, *args):
        log.msg('Command failed')
        log.msg(args)

class ServerFactory(protocol.ServerFactory):
    listen_port = 8500

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        assign_attrs(self, **kwargs)
        self.host = Host()
    
    def buildProtocol(self, addr):
        return ServerProtocol(self)
    
    def start(self):
        # start main server
        self.setup_host()
        app.reactor.listenTCP(self.listen_port, self)
        log.msg('TCP Server listening on port %s' % self.listen_port)
    
    def connectionMade(self, server):
        pass

    def setup_host(self):
        ''' conditionally generate host info '''
        host = self.host
        address = get_address()
        if address == host.address or address == None:
            return
        host.address = address
        host.tcp_port = self.listen_port
        host.udp_port = app.udp_server.listen_port
        host.signed_at = host.time_now()
        host.pubkey_str = app.node.auth.pubkey_str
        host.signature = app.node.auth.sign(host.signature_data)
    
    @property
    def address(self):
        return self.host.address

    def check_address(self):
        ''' unconditionally recreate host information '''
        self.address = None
        self.setup_host()

    @property
    def host_args(self):
        '''
            dict of host
        '''
        return self.host.to_dict()
    
def simple_router(resource, server, **kwargs):
    for k in kwargs.keys():
        if kwargs[k] != None:
            return getattr(resource, k)(server, kwargs[k])
