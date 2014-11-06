from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log

import rainmaker_app
from rainmaker_app import app
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app.lib.net import connections
from rainmaker_app.lib.net.resources import files_resource, messages_resource 
from rainmaker_app.db.models import *

from .net_utils import is_compatible, get_address, \
    report_errors
from .exceptions import *
from .commands import *
from .session import Session, require_secure

class ServerProtocol(amp.AMP):
    '''
        c->s: connect
        c->s: check version
        c->s: set_pubkey
        c->s: startTLS
        c->s: set salt
        c->s: authenticate
    '''
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        log.msg('Connection Made')
        self.addr_port = self.transport.getHost()
        self.session = Session(app.auth)
        connections.add(self)

    def connectionLost(self, reason):
        log.msg('Connection Lost')
        connections.remove(self)
    ####
    #
    ####
    @require_secure
    def connection_secure(self):
        log.msg('The connection is now secure')  

    def command_failed(self, *args):
        log.msg('Command failed')
        log.msg(args)

    ####
    #
    ####
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
    
    ####
    #
    ####
    @PingCommand.responder
    def ping_command_responder(self):
        log.msg('Server: received ping')
        return {'code':200}
    
    @require_secure
    @SecurePingCommand.responder
    def secure_ping_command_responder(self):
        log.msg('Server: received secure ping')
        return {'code':200}

    @VersionCheckCommand.responder
    def version_check_command_responder(self, version):
        log.msg('Server: client version: %s' % version)
        return {
            'response_code':200,
            'version': app.version
        }

    ####
    # Authentication functions
    ####
    @SetPubkeyCommand.responder
    def set_pubkey_command_responder(self, cert):
        log.msg('Server: Received cert')
        log.msg("SERVER: Here is what we received:")
        log.msg(cert)
        self.session.peer_cert = cert
        return {'cert': self.session.auth.cert_str}
    
    @amp.StartTLS.responder
    def startTLS_responder(self):
        log.msg( "Server: We are starting TLS" )
        return self.session.certParams()
     
    @require_secure
    @AuthCommand.responder
    @defer.inlineCallbacks
    def auth_command_responder(self, rand, guid, enc_pass):
        log.msg('Server: running AuthCommand')
        self.session.sync_path = yield SyncPath.find(where=["guid = ?", guid], limit=1)
        result = self.session.authorize(rand, enc_pass)
        defer.returnValue(result)

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
        #host.pubkey_str = app.node.auth.pubkey_str
        #host.signature = app.node.auth.sign(host.signature_data)
    
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
