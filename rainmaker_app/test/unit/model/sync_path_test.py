from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class SyncPathTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/model/sync_path_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
 
    @inlineCallbacks
    def test_refresh_state_hash(self):
        sync_path = yield SyncPath.find(limit=1)
        state = yield sync_path.refresh_state_hash()
        yield MyFile(is_dir=False,path='df',sync_path_id=1, fhash='3578').save()
        is_stale = yield sync_path.is_state_hash_stale()
        self.assertEquals(is_stale, True)
        new_state = yield sync_path.refresh_state_hash()
        self.assertEquals( new_state != state, True)

    def test_ability_to_scan(self):
        '''
            test ability to scan files
        '''

