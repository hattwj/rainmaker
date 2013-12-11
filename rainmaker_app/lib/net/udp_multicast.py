# Simple UDP Multicast Server example
# Kyle Robertson
# A Few Screws Loose, LLC
# http://www.afslgames.com
# ra1n@gmx.net
# MulticastServer.py

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.application.internet import MulticastServer

from rainmaker_app import app

############################################
app_key = 'rain,%s,%s' % (app.version, app.guid)
###########################################

class MulticastServerUDP(DatagramProtocol):
    def startProtocol(self):
        print 'Started Listening'
        # Join a specific multicast group, which is the IP we will respond to
        self.transport.joinGroup(app.multicast_group)

    def datagramReceived(self, datagram, address):
        # The uniqueID check is to ensure we only service requests from ourselves
        if udp_filter( datagram, address):
            return
        print "Server Received:" + repr(datagram)
        self.transport.write("data", address)

#############################################################################
# Simple UDP Multicast Client example
# Kyle Robertson
# A Few Screws Loose, LLC
# http://www.afslgames.com
# ra1n@gmx.net
# MulticastClient.py

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.application.internet import MulticastServer

class MulticastClientUDP(DatagramProtocol):

    def datagramReceived(self, datagram, address):
        if udp_filter( datagram, address):
            return
        print "--Received:" + repr(datagram)
        print address

def udp_filter( datagram, address):
    return True
    if datagram.startswith( app_key ):
        return False
    
def broadcast_loop():
    # Sample request:
    request = '%s,hostid' % app_key
    
    # Send multicast on 224.0.0.1:8005, on our dynamically allocated port
    app.udp_broadcast.write(request, (app.multicast_group, app.udp_port)) 

    if app.running == True:
        app.reactor.callLater(0.5, broadcast_loop)     
