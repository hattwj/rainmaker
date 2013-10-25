from OpenSSL import SSL

from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol

from twisted.python.log import err
from twisted.web.client import Agent
from twisted.internet import reactor, ssl

import cert

class CtxFactory(ssl.ClientContextFactory):
    c_path = None
    k_path = None

    def getContext(self, v1,v2):
        self.method = SSL.SSLv23_METHOD
        ctx = ssl.ClientContextFactory.getContext(self)

        ctx.use_certificate_file(self.c_path)
        ctx.use_privatekey_file(self.k_path)

        ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
            cert.verifyCallback
            )

        # Since we have self-signed certs we have to explicitly
        # tell the server to trust them.
        ctx.load_verify_locations(self.c_path)
        return ctx

class simplePrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10
 
    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            print display
            self.remaining -= len(display)
 
    def connectionLost(self, reason):
        self.finished.callback(None)
 
class SSLClient(object):
    def __init__(self, k_path, c_path):
        self.ctx_factory = CtxFactory()
        self.ctx_factory.c_path = c_path
        self.ctx_factory.k_path = k_path

    def request(self, action, url):
        agent = Agent(reactor, self.ctx_factory)
        print dir(agent)
        d = agent.request(action, url)
        d.addCallbacks(self.response_handler, err)
        return d

    def response_handler(self, response):
        print "Received response"
        print dir(response)
        if (response.code == 200):
            finished = Deferred()
            response.deliverBody(simplePrinter(finished))
            return finished
        else:
            print 'Response code:', response.code
        
