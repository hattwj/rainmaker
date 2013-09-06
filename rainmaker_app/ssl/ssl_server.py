from OpenSSL import SSL
from twisted.internet import ssl, reactor
from twisted.internet.protocol import Factory, Protocol

from twisted.web import static, server
from twisted.web.resource import Resource

class Hello(Resource):

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        return '<html>Hello, GET world! I am located at %r. </html>' \
                % (request.prepath)

class Echo(Protocol):
    def dataReceived(self, data):
        self.transport.write(data)

def verifyCallback(connection, x509, errnum, errdepth, ok):
    if not ok:
        print 'invalid cert from subject:', x509.get_subject()
        return False
    else:
        print "Server: Client certs are fine"
    return True

if __name__ == '__main__':
    #factory = Factory()
    #factory.protocol = Echo
    
    site = server.Site(Hello())

    myContextFactory = ssl.DefaultOpenSSLContextFactory(
        'server.key', 'server.crt'
        )

    ctx = myContextFactory.getContext()

    ctx.set_verify(
        SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
        verifyCallback
        )

    # Since we have self-signed certs we have to explicitly
    # tell the server to trust them.
    ctx.load_verify_locations("server.crt")

    #reactor.listenSSL(8000, factory, myContextFactory)
    reactor.listenSSL(8000, site, myContextFactory)
    reactor.run()
