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
        request = DatagramParser(local, 'rain:%s,store_host:{"pubkey":"bar","address":"127.0.0.1","port":12345,"signature":"abcdefg"}' % app.version)
        self.assertEquals(None, request.error)

        request = DatagramParser(['127.0.0.1',4000],'rain:%s,store:{"key":"12345678","val":"Somevalhere"}' % app.version) 
        self.assertEquals(None, request.error)

        request = DatagramParser(['127.0.0.1',4000],'rain:%s,find:{"key":"12345678"}' % app.version) 
        self.assertEquals(None, request.error)

    def test_filters(self):
        # Filter on Empty datagram
        request = DatagramParser(['127.0.0.1', 4000], '')
        self.assertEquals(request.error, request.ERR_EMPTY)
        # Filter on bad client id
        request = DatagramParser(['127.0.0.1', 4000],'snow:%s,find:{"key":"12345678"}' % app.version)
        self.assertEquals(request.error, request.ERR_PROTOCOL)
        # Filter on malformed parameter data
        request = DatagramParser(['127.0.0.1', 4000],'rain:%s,find:"key"' % app.version)
        self.assertEquals(request.error, request.ERR_MALFORMED)

    def test_encoder(self):
        msg = DatagramParser.encode('find',key='aaa')
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
        self.protocol = MulticastServerUDP(listen_port=port, node={'key_size':512})
        self.transport = FakeTransport()
        self.protocol.transport = self.transport
        self.protocol.startProtocol()

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
        self.protocol.shutdown()
    
    # Tests 
    def test_store_host_command(self):
        # aliases
        p = self.protocol
        t = self.transport 
        # add hosts
        msgs = []
        for i in range(0,10):
            msg = 'rain:%s:set_host:guid%s:%s:%s' % \
                (app.version,i, remote[0], remote[1])
            err = p.datagramReceived(msg, remote)
            self.assertEquals(err, p.ERR_NONE)
            # buffer will send to remote2
            msgs.append([msg,remote2])
        # request hosts
        msg = 'rain:%s:get_hosts' % (app.version)
        err = p.datagramReceived(msg, remote2)
        self.assertEquals(err, p.ERR_NONE)
        # check buffer
        self.assertEqual(len(t.msgs), 10)
        for m in t.msgs:
            self.assertEqual( m in msgs, True) 

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

class DHTNodeTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/net/dht_node_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )
        self.protocol = FakeProtocol()
        self.node = DHTNode(self.protocol, key_size=512)

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
        self.node.shutdown()

    def test_host_count(self):
        node = self.node
        self.assertEquals(0, node.host_count())

class FakeProtocol(object):
    pass
