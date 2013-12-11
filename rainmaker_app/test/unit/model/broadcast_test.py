from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class BroadcastTest(unittest.TestCase):

# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir() 
        yield initDB(db_path)

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
    @inlineCallbacks
    def test_uniqueness_validation(self):
        b = yield Broadcast(host_id=1,message_id=1).save()
        self.assertEquals(b.errors.isEmpty(), True)

        b = yield Broadcast(host_id=1,message_id=1).save()
        self.assertEquals(b.errors.isEmpty(), False)

def mock_router( broadcast ):
    print 'broadcast recieved'

Broadcast.router = mock_router

