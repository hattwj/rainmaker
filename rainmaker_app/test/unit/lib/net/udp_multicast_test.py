from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.net import udp_multicast

# stub out module import
fake_host = '127.0.0.1'
def get_fakeaddress(addr=None):
    return fake_host
udp_multicast.get_address = get_fakeaddress
from rainmaker_app.lib.net.udp_multicast import *

port = 444
local = (fake_host, port,) 
remote = ('192.168.0.2', port,) 
remote2 = ('192.168.0.3', port,) 

class DatagramParserTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)

    def test_commands(self):
        request = DatagramParser(local, 'rain:%s,announce:{"tcp_port":12345}' % app.version)
        self.assertEquals(None, request.error)

    def test_filters(self):
        # Filter on Empty datagram
        request = DatagramParser(['127.0.0.1', 4000], '')
        self.assertEquals(request.error, request.ERR_EMPTY)
        # Filter on bad client id
        request = DatagramParser(['127.0.0.1', 4000],'snow:%s,find:{"key":"12345678"}' % app.version)
        self.assertEquals(request.error, request.ERR_PROTOCOL)
        # Filter on unknown action
        request = DatagramParser(['127.0.0.1', 4000],'rain:%s,unknown_action:{"key":44}' % app.version)
        self.assertEquals(request.error, request.ERR_ACTION)
        # Filter on malformed action parameters
        request = DatagramParser(['127.0.0.1', 4000],'rain:%s,announce:{"key":44}' % app.version)
        self.assertEquals(request.error, request.ERR_ARGS)

    def test_encoder(self):
        msg = DatagramParser.encode('announce',tcp_port='1234')
        request = DatagramParser(['127.0.0.1', 4000], msg)
        self.assertEquals(request.error, request.ERR_NONE)
        
class MulticastServerUDPTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/net/udp_multicast_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )
        self.protocol = MulticastServerUDP(8000, listen_port=port)
        self.transport = FakeTransport()
        self.protocol.transport = self.transport
        self.protocol.startProtocol()

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
    # Tests
    def test_announce_command(self):
        ''' test ability to receive and process announce command '''
        # aliases
        p = self.protocol
        t = self.transport 
        
        p.client_factory = FakeClientFactory()

        # announce host
        msg = DatagramParser.encode('announce', tcp_port=8000)
        err = p.datagramReceived(msg, remote2)
        self.assertEquals(err, p.ERR_NONE)
        
        # check for response
        host = p.client_factory._host
        self.assertEquals(host==None, False)
        self.assertEquals(host.tcp_port, 8000)
        self.assertEquals(host.address, remote2[0])
    #TODO: Add tests

##############################
# Fake objects for testing
##############################

class FakeTransport(object):
    def __init__(self):
        self._msgs = []
    def write(self, msg, addr_port):
        self._msgs.append( [msg, addr_port] )
    def clear(self):
        self._msgs = []

    @property
    def msgs(self):
        ''' messages sent by server '''
        return self._msgs

    def getHost(self):
        return FakeHostInfo()

    def joinGroup(self, *args):
        pass

class FakeHostInfo(object):
    host = local
    port = port

class FakeClientFactory(object):
    _host = None

    def dht_client(self, host):
        self._host = host
