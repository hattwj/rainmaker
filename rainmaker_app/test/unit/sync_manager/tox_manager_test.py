from twisted.trial import unittest
from twisted.internet import defer

from rainmaker_app.test import test_helper
from rainmaker_app.test import db_helper

from rainmaker_app.sync_manager.tox_manager import ToxManager
from rainmaker_app.conf import initializers
from rainmaker_app.db.models import SyncPath

class ToxManagerTest(unittest.TestCase):
    
    @defer.inlineCallbacks
    def setUp(self):
        test_helper.clean_temp_dir()
        yield db_helper.initDB(test_helper.db_path)
        tox_html = test_helper.load('test/fixtures/tox_nodes.html', raw=True)
        yield initializers.tox.configure(tox_html=tox_html)

    @defer.inlineCallbacks
    def tearDown(self):
        yield db_helper.tearDownDB()
  
    @defer.inlineCallbacks
    def test_can_save_data(self):
        sync_path = SyncPath()
        tm = ToxManager(sync_path)
        #tm.start()
        
