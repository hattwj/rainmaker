from rainmaker_app.test import db_helper
from rainmaker_app.test import test_helper

class ToxManagerTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        test_helper.clean_temp_dir()
        yield db_helper.initDB(test_helper.db_path)
        #self.data = load('test/fixtures/unit/sync_manager/tox_manager_test.yml')
        #yield load_fixture( 'setup', self.data )
        #yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield db_helper.tearDownDB()
 

