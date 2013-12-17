from twisted.internet import protocol, reactor, ssl, defer
from twisted.protocols import amp
from twisted.python import log

import rainmaker_app
from rainmaker_app.lib.net.commands import *
from rainmaker_app.lib.net.resources import files_resource, messages_resource 
from rainmaker_app.db.models import Authorization, MyFile, Broadcast

from .net_utils import is_compatible

class AuthRequired(Exception):
    pass

class StartTLSFailed(Exception):
    pass

def require_secure(func):    
    ''' decorator '''
    def sub_require_secure(self, *args, **kwargs):
        ''' nested func to access func parameters'''
        t = self.transport
        if hasattr(t,'getPeerCertificate') and t.getPeerCertificate():
            # run
            d = func(self, *args, **kwargs)
            return d # string
        else:
            raise AuthRequiredError() 
    return sub_require_secure

class ServerProtocol(amp.AMP):
    authorization = None     
    sync_path = None # Set after authentication

    def __init__(self, **kwargs):
        self.authorization = None

    @VersionCheckCommand.responder
    def version_check(self, version):
        log.msg('client version: %s' % version)
        return {
            'response_code':200,
            'version': rainmaker_app.version
        }

    def connectionMade(self):
        pass
        #Broadcast.add_listener( self )

    def connectionLost(self, reason):
        log.msg(reason)
        #Broadcast.remove_listener( self )

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
        print 'The connection is now secure' 
        
    @require_secure
    @FilesResource.responder
    def files_resource(self, **kwargs):
        @defer.inlineCallbacks
        def sub_files_resource(self, **kwargs):
            self.sync_path = yield self.authorization.sync_path.get()
            result = yield simple_router(files_resource, self, **kwargs)
            defer.returnValue(result)
        return sub_files_resource(self, **kwargs)
    
class ServerFactory(protocol.ServerFactory):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def buildProtocol(self, addr):
        return ServerProtocol(**self.kwargs)

class ClientProtocol(amp.AMP):
    server_version = None
    authorization = None
    certParams = None
    after_auth = None

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def connectionMade(self):
        ''' '''
        d = self.version_check()
        d.addCallback(self.set_pubkey)
        d.addCallback(self.start_tls)
        d.addErrback(self.startup_failed)

        if self.after_auth:
            d.addCallback( self.after_auth, self)

    @defer.inlineCallbacks
    def version_check(self):
        result = yield self.callRemote( VersionCheckCommand, version = rainmaker_app.version)
        if not is_compatible(result['version']):
            raise StartTLSFailed('Incompatible Version: %s' % result['version'])
        log.msg(result)

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
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def buildProtocol(self, addr):
        return ClientProtocol( **self.kwargs)

    def clientConnectionFailed(self, connector, reason):
        print "connection failed: ", reason.getErrorMessage()

    def clientConnectionLost(self, connector, reason):
        print "connection lost: ", reason.getErrorMessage()


def simple_router(resource, server, **kwargs):
    for k in kwargs.keys():
        if kwargs[k] != None:
            return getattr(resource, k)(server, kwargs[k]) 

