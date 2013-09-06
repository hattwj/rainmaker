from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class DbSyncPathTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        print 'Running'


    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()


    @inlineCallbacks
    def test_select(self):
        self.sync_path = yield SyncPath(root=data_dir).save()
