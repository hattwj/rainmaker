from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *
from rainmaker_app.lib.net.dht_node import *

data = None

class DHTNodeTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        global app
        global data
        clean_temp_dir()
        yield initDB(db_path)
        data = load('test/fixtures/unit/lib/net/dht_node_test.yml')
        yield load_fixture( 'setup', data )
        yield load_fixture( self._testMethodName, data )
        
        auth = Authorization(key_size=512)
        self.node = DHTNode(auth)
        app.client = FakeProtocol(self.node)
        app.reactor = FakeReactor()
        app.client.node = self.node

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
        self.node.shutdown()
        
    def assert_host_count(self, count):
        self.assertEquals(0, selfnode.host_count())
    
    @defer.inlineCallbacks
    def test_hosts_find(self):
        '''
           - verify node finds hosts
           - watch behavior as nodes added
           -- max nodes
           -- min nodes
           -- node count per bucket
           --- blind spots
           a single node should allow us to
           progressively search for more nodes
           until min nodes reached
        '''
        node = self.node
        self.assert_hosts_count(0)
        

        node.__hosts_find__()
        
class FakeProtocol(object):
    
    def __init__(self, node):
        self.node = node

    def send_find_host(self, to_host, node_id):
        host_data = data['find_host']
        key = ':'.join(*to_host.addr_port)
        if key not in host_data.keys():
            return
        if node_id not in host_data[key].keys():
            return
        for kwargs in host_data[key][node_id]:
            self.node.store_host(**kwargs)

class FakeReactor(object):
    def callLater(self, *args, **kwargs):
        pass

class FakeHost(Host):
    ''' 
    FakeHost:  
        Allows us to generate hosts with arbitrary node ids
    '''
    
    @classmethod
    def RandomHost(self, node_exp):
        


