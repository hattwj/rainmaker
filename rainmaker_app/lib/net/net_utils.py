import errno
from socket import error as socket_error
from twisted.python import log
from twisted.internet import defer
from rainmaker_app import app
from .exceptions import AuthRequiredError

###################################
# Utility functions
###################################
def require_secure(func):    
    ''' decorator to require secure connection '''
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

def report_errors(func):    
    ''' decorator to catch amp command errors  '''
    def sub_report_errors(self, *args, **kwargs):
        ''' nested func to access func parameters'''
        print 'd:'
        # run
        d = defer.Deferred()
        d.addCallback(func, self, *args, **kwargs)
        print d
        return d
    return sub_report_errors

def is_compatible(ver):
    ''' Is the current version of the application compatible with `ver`'''
    try:
        if app.version.split('.')[0:2] == ver.split('.')[0:2]:
            return True
    except:
        pass
    return False

from twisted.internet.protocol import DatagramProtocol
class AddressServerUDP(DatagramProtocol):
    ''' get address '''
    address = '224.0.0.0'
    listen_port = 0    
    host = None
    
    def __init__(self, address=None):
        if address: self.address = address

    def get_address(self):
        # Join a specific multicast group, which is the IP we will respond to
        #print self.transport.getHost()
        self.transport.connect( self.address, self.listen_port)
        host = self.transport.getHost()
        return host.host

def get_address(address=None):
    serv = AddressServerUDP(address)
    try:
        app.reactor.listenMulticast(serv.listen_port, serv)
        address = serv.get_address()
    except socket_error as serr:
        # is the muticast unreachable?
        if serr.errno != errno.ENETUNREACH:
            # Not the error we are looking for, re-raise
            raise serr
        log.err('Unable to detect our address')
        address = None
    # make sure we close connection to prevent memory leak
    serv.transport.loseConnection()
    return address
