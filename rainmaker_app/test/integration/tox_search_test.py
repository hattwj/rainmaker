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

    @defer.inlineCallbacks
    def tearDown(self):
        yield db_helper.tearDownDB()
    
    def on_tox_event(self, event):
        self.primary_fired = True
        self.sb.stop()
        self.pb.stop()

    @defer.inlineCallbacks
    def test_can_find_primary_node(self): 
        pb = tox_ring.PrimaryBot()
        sb = tox_ring.SyncBot(pb.get_address())
        sb.events.register('tox_search_completed', self.on_tox_event)
        self.sb = sb
        d = sb.start()
        dd = pb.start()
        self.pb = pb
        yield d
        yield dd
        self.assertEquals(self.primary_fired, True)

