from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

class HostTest(unittest.TestCase):

# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/model/host_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    @inlineCallbacks
    def test_guid(self):
        ''' no difference between sets '''
        a = Authorization(key_size=512)
        h = Host()
        h.pubkey_str = a.pubkey_str
        print h.node_id
        h.address='127.0.0.1'
        h.tcp_port=40
        h.udp_port=30
        h.signature = a.sign(h.signature_data)
        yield h.save()
        gg = yield Host.all()
        print gg


