from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log

import rainmaker_app
from rainmaker_app import app
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app.lib.net.resources import files_resource, messages_resource 
from rainmaker_app.db.models import *

from .net_utils import is_compatible, require_secure, get_address, \
    report_errors
from .exceptions import *
from .commands import *

class ServerProtocol(amp.AMP):
    authorization = None     
    sync_path = None # Set after authentication

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        log.msg('Connection Made')
        # notify factory
        self.factory.connectionMade(self)
        # ask for client information
        self.callRemote(PingHostCommand)

    def connectionLost(self, reason):
        log.msg('Connection Lost')
        log.msg(reason)
    
    @FindHostCommand.responder
    def find_host_command(self, **kwargs):
        hosts = app.node.find_nearest_hosts(**kwargs)
        for host in hosts:
            self.callRemote(StoreHostCommand, **host.to_dict() )
        return {'code', 200}

    @StoreHostCommand.responder
    @defer.inlineCallbacks
    def store_host_command(self, **kwargs):
        d = app.node.store_host(**kwargs)
        d.addErrback( self.command_failed )
        yield d
        defer.returnValue( {
            'code': 200,
            'errors' : []
        })

    @VersionCheckCommand.responder
    def version_check(self, version):
        log.msg('client version: %s' % version)
        return {
            'response_code':200,
            'version': app.version
        }

    @SetPubkeyCommand.responder
    def set_pubkey(self, guid):
        log.msg(guid)    # log request
        self.authorization = None # clear params
        self.sync_path = None 
        @defer.inlineCallbacks
        def sub_set_pubkey(self, guid):
            auth = yield Authorization.find(where=['guid = ?',guid],limit=1)
            if auth:
                self.authorization = auth
                defer.returnValue( {'response_code':200,'message':'Found pubkey'} )
            else:
                defer.returnValue( {'response_code':404,'message':'Unknown pubkey'} )
        return sub_set_pubkey(self, guid)
    
    @PostMessageCommand.responder
    def post_message_command(self, **kwargs):
        return messages_resource.post( self, **kwargs) 
    
    @GetMessagesCommand.responder
    def get_messages_command(self, **kwargs):
        return messages_resource.get( self, **kwargs) 

    @amp.StartTLS.responder
    def startTLS(self):
        log.msg( "server: We started TLS" )
        return self.authorization.certParams()
 
    @require_secure
    def connection_secure(self):
        log.msg('The connection is now secure') 
    
    @require_secure
    @FilesResource.responder
    def files_resource(self, **kwargs):
        @defer.inlineCallbacks
        def sub_files_resource(self, **kwargs):
            self.sync_path = yield self.authorization.sync_path.get()
            result = yield simple_router(files_resource, self, **kwargs)
            defer.returnValue(result)
        return sub_files_resource(self, **kwargs)

    @PingHostCommand.responder
    def ping_host_command(self):
        log.msg('sending host')
        kwargs = app.server.host_args
        print kwargs
        d = self.callRemote(StoreHostCommand, **kwargs)
        d.addErrback(self.commandFailed)
        return {'code':200}

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
        return self.host.to_dict()
    
def simple_router(resource, server, **kwargs):
    for k in kwargs.keys():
        if kwargs[k] != None:
            return getattr(resource, k)(server, kwargs[k])
