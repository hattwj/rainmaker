from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *
from rainmaker_app.lib.net.dht_node import *

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
    
    @defer.inlineCallbacks
    def test_host_count(self):
        node = self.node
        self.assertEquals(0, node.host_count())
        ff = yield Authorization.all()

class FakeProtocol(object):
    pass

