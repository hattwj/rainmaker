from twisted.internet import defer

from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *
#app.auth = Authorization(key_size=512)

data = None

class StartTLSTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        yield initDB(db_path)

    @defer.inlineCallbacks
    def tearDown(self):
        yield None
 
    def test_hosts_find(self):
        d = defer.Deferred()
