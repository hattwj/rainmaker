from twisted.trial import unittest
from twisted.internet import defer, reactor

from rainmaker_app.test import test_helper
from rainmaker_app.test import db_helper
from rainmaker_app.tox import tox_ring, tox_env
from rainmaker_app.conf import initializers

class ToxSearchTest(unittest.TestCase):
    
    @defer.inlineCallbacks
    def setUp(self):
        #test_helper.clean_temp_dir()
        yield db_helper.initDB(test_helper.db_path)
        tox_html = test_helper.load('test/fixtures/tox_nodes.html', raw=True)
        yield initializers.tox.configure(tox_html=tox_html)
        self.primary_fired = False
        #self.data = load('test/fixtures/unit/sync_manager/tox_manager_test.yml')
        #yield load_fixture( 'setup', self.data )
        #yield load_fixture( self._testMethodName, self.data )

    @defer.inlineCallbacks
    def tearDown(self):
        yield db_helper.tearDownDB()
    
    def on_start_primary(self):
        self.primary_fired = True
    
    @defer.inlineCallbacks
    def test_can_find_primary_node(self):
        pb = tox_ring.PrimaryBot()
        sb = tox_ring.SyncBot(pb.get_address())
        sb.on_start_primary = self.on_start_primary
        d = sb.start()
        pb.start()
        yield d
        pb.stop()
        self.assertEquals(self.primary_fired, True)

