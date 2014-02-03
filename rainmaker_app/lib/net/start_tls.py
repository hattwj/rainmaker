from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log

import rainmaker_app
from rainmaker_app import app
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app.lib.net.resources import files_resource, messages_resource 
from rainmaker_app.db.models import *

from .net_utils import is_compatible, require_secure, get_address
from .exceptions import *
from .commands import *

class ServerProtocol(amp.AMP):
    authorization = None     
    sync_path = None # Set after authentication

    def __init__(self):
        pass

    def connectionMade(self):
        log.msg('Connection Made')

    def connectionLost(self, reason):
        log.msg(reason)

    @StoreHostCommand.responder
    def store_host_command(self, **kwargs):
        host = Host(**kwargs)
        self.node.store_host( host )

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
       self.sendCommand(StoreHostCommand, app.server.host_args())   

class ServerFactory(protocol.ServerFactory):
    listen_port = 8500
    __host__ = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        assign_attrs(self, **kwargs)
        self.__host__ = Host()
    
    def buildProtocol(self, addr):
        return ServerProtocol()
    
    def start(self):
        # start main server
        self.setup_host()
        app.reactor.listenTCP(self.listen_port, self)
        log.msg('TCP Server listening on port %s' % self.listen_port)

    def setup_host(self):
        host = self.__host__
        address = get_address()
        if address != host.address or address == None:
            return
        host.address = address
        host.tcp_port = self.listen_port
        host.udp_port = app.udp_server.listen_port
        host.nonce = host.time_now()
        host.signature = app.node.auth.sign(host.signature_data)
        self.host_args = self.__host__.to_json()
    
    @property
    def address(self):
        return self.__host__.address
    
def simple_router(resource, server, **kwargs):
    for k in kwargs.keys():
        if kwargs[k] != None:
            return getattr(resource, k)(server, kwargs[k])
