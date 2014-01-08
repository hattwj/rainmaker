from rainmaker_app import app

def is_compatible(ver):
    ''' Is the current version of the application compatible with `ver`'''
    try:
        if app.version.split('.')[0:2] == ver.split('.')[0:2]:
            return True
    except:
        pass
    return False

from twisted.internet.protocol import DatagramProtocol
from .net_utils import is_compatible

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
        self.transport.loseConnection()
        return host.host

def get_address(address=None):
    serv = AddressServerUDP(address)
    app.reactor.listenMulticast(serv.listen_port, serv)
    return serv.get_address()

