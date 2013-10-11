from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

class DifferenceTest(unittest.TestCase):

# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/model/difference_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
    @inlineCallbacks
    def test_no_conflict(self):
        ''' no difference between sets '''
        g = yield Difference.between_sync_paths(1, 2)
        self.assertEquals( g, [] )
    
    @inlineCallbacks
    def test_deleted(self):
        g = yield Difference.between_sync_paths(1, 2)
        self.assertEquals( len(g), 2)