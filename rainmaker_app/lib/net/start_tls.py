from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
#from twisted.python import log

import rainmaker_app
from rainmaker_app import app
from rainmaker_app.lib.util import assign_attrs, time_now
from rainmaker_app.lib.net import connections
from rainmaker_app.lib.net.resources import files_resource
from rainmaker_app.db.models import *
from rainmaker_app.lib import logger
log = logger.create(__name__)

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
    @SetGetHostCommand.responder
    @defer.inlineCallbacks
    def set_get_host_command_responder(self, **kwargs):
        log.msg('Server: Received host info')
        log.msg("SERVER: Here is what we received:")
        log.msg(kwargs)
        host = Host(**kwargs)
        yield host.save()
        self.session.host = host
        defer.returnValue(self.factory.host_params)
    
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
    
    @require_secure
    @GetHostsCommand.responder
    @defer.inlineCallbacks
    def get_hosts_command_responder(self, guid):
        '''
            return our host or find host
        '''
        keys = GetHostsCommand.responder_keys()
        @defer.inlineCallbacks
        def _get_host(guid):
            host = yield Host.find(where=['guid = ?', guid], limit=1)
            if host:
                result = host.to_dict(keys)
                defer.returnValue([result])
            else:
                raise ErrNotImplemented('finger lookups not ready')
        if guid:
            return _get_host(guid)
        else:
            return [self.factory.host.to_dict(keys)]
    @require_secure
    @PutHostsCommand.responder
    def put_hosts_command_responder(self, hosts):
        for host_params in hosts:
            host = Host(**host_params)
            host.save()

    ####
    # Sync functions
    ####
    @require_secure
    @GetSyncPathCommand.responder
    @defer.inlineCallbacks
    def get_sync_path_command_responder(self, **kwargs):
        hsp = yield HostSyncPath.findOrCreate(
            machine_name=kwargs['machine_name'], 
            sync_path_id = self.session.sync_path.id,
            host_id = self.session.host.id
        )
        hsp.state_hash = kwargs['state_hash']
        hsp.rolling_hash = kwargs['rolling_hash']
        attrs = GetSyncPathCommand.response_keys()
        defer.returnValue(self.session.sync_path.to_dict(attrs))

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
        host.signed_at = time_now()
        host.cert_str = app.auth.cert_str
        host.pubkey_str = app.auth.pubkey_str
        host.signature = app.node.auth.sign(host.signature_data)
    
    @property
    def address(self):
        return self.host.address

    def check_address(self):
        ''' unconditionally recreate host information '''
        self.address = None
        self.setup_host()

    @property
    def host_params(self):
        '''
            dict of host
        '''
        return self.host.to_dict(host_param_keys) 
