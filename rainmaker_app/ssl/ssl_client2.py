from OpenSSL import SSL

from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol

from twisted.python.log import err
from twisted.web.client import Agent
from twisted.internet import reactor, ssl
from twisted.internet.ssl import ClientContextFactory

class CtxFactory(ClientContextFactory):
    def getContext(self, v1,v2):
        self.method = SSL.SSLv23_METHOD
        ctx = ssl.ClientContextFactory.getContext(self)
        # use_certificate and use_privatekey for raw data
    
        ctx.use_certificate_file('server.crt')
        ctx.use_privatekey_file('server.key')

        ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
            verifyCallback
            )

        # Since we have self-signed certs we have to explicitly
        # tell the server to trust them.
        ctx.load_verify_locations("server.crt")

        return ctx

def verifyCallback(connection, x509, errnum, errdepth, ok):
    if not ok:
        print 'invalid cert from subject:', x509.get_subject()
        return False
    else:
        print "Client: Sever certs are fine"
    return True


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
 
 
def cbResponse(response):
    if (response.code == 200):
        finished = Deferred()
        response.deliverBody(simplePrinter(finished))
        return finished
    else:
        print 'Response code:', response.code


def display(response):
    print "Received response"
    print dir(response)

def main():
    url = 'https://localhost:8000/sync_path'
    factory = CtxFactory()
    agent = Agent(reactor, factory)
    d = agent.request("GET", url)
    #d.addCallbacks(display, err)
    d.addCallbacks(cbResponse, err)
    d.addCallback(lambda ignored: reactor.stop())
    reactor.run()

if __name__ == "__main__":
    main()
