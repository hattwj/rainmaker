from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *
from rainmaker_app.lib.net import udp_multicast

class HostTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
    # Tests 
    def test_pubkey(self):
        auth = Authorization(key_size=512)
        host = Host(address='127.0.0.1', 
            udp_port=4000, 
            tcp_port=5000,
            pubkey_str=auth.pubkey_str)
        host.signature = auth.sign( host.signature_data )
        valid = host.verify_sig()
        self.assertEquals(True, valid)
