from OpenSSL import SSL
from twisted.internet import ssl, reactor
from twisted.internet.protocol import Factory, Protocol

from twisted.web import static, server
from twisted.web.resource import Resource

import routes
import cert

class SSLServer(object):

    def __init__(self):
        self.resources = routes.resources()
        self.site = server.Site(self.resources)
        self.port = 3000
        self.port_obj = None
        self.k_path = None
        self.c_path = None
        self.ctx = None

    def start(self):
    
        # set key/cert for our server
        myContextFactory = ssl.DefaultOpenSSLContextFactory(self.k_path, self.c_path)
        self.ctx = myContextFactory.getContext()
    
        self.ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
            cert.verifyCallback
        )
    
        # Since we have self-signed certs we have to explicitly
        # tell the server to trust them.
        self.ctx.load_verify_locations(self.c_path)
        self.port_obj = reactor.listenSSL(self.port, self.site, myContextFactory)

    def stop(self):
       self.port_obj.stopListening() 

#if __name__ == '__main__':
#    run()
#    reactor.run()
