from twisted.trial import unittest
from twisted.internet import defer

from rainmaker_app.test import test_helper
from rainmaker_app.test import db_helper
from rainmaker_app.tox import tox_ring

class ToxSearchrTest(unittest.TestCase):
    
    @defer.inlineCallbacks
    def setUp(self):
        test_helper.clean_temp_dir()
        yield db_helper.initDB(test_helper.db_path)
        #self.data = load('test/fixtures/unit/sync_manager/tox_manager_test.yml')
        #yield load_fixture( 'setup', self.data )
        #yield load_fixture( self._testMethodName, self.data )

    @defer.inlineCallbacks
    def tearDown(self):
        yield db_helper.tearDownDB()
 
    @defer.inlineCallbacks
    def test_can_find_primary_node(self):
        pb = tox_ring.PrimaryBot()
        sb = tox_ring.SyncBot(pb.get_address())
        sb.start()
