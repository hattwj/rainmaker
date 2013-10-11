from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.conflict_manager.sync_path_resolver import \
    SyncPathResolver, _get_file_from, _resolver_info, TooManyFilesError, \
    NoActionError, NoResolverError, NoFilesError
from rainmaker_app.lib.conflict_manager.file_resolver import FileResolver

# Mock classes and helper functions

class MockFileResolver(object):
    
    def __init__(self, data=None):
        self.last_child = self
        self.conflict_files = []

class MockTransferAgent(object):
    
    def create(self, sync_path, my_file):
        return 'create: %s-%s for %s' % (my_file.sync_path_id, my_file.path, sync_path.id)

    def update(self, sync_path, my_file):
        return 'update: %s-%s for %s' % (my_file.sync_path_id, my_file.path, sync_path.id)

    def delete(self, sync_path, my_file):
        return 'create: %s-%s for %s' % (my_file.sync_path_id, my_file.path, sync_path.id)

    def move(self, sync_path, my_file):
        return 'create: %s-%s for %s' % (my_file.sync_path_id, my_file.path, sync_path.id)

mock_objs = {
    'mock_file_resolver': MockFileResolver,
    'mock_transfer_agent': MockTransferAgent,
    'my_file': MyFile,
    'sync_path': SyncPath,
    'str': str,
    'int': int
}

class SyncPathResolverTest(unittest.TestCase):
    
# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/conflict_manager/sync_path_resolver.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()

    # Tests class methods    
    @inlineCallbacks
    def test_resolve_against(self):
        # def resolve_against(self, sync_paths_arr): 
        fail

    # Tests class instance methods
    def test_init(self):
        # def __init__(self, transfer_agent):
        x = MockTransferAgent()
        y = SyncPathResolver(x)
    
    @inlineCallbacks
    def test_conflicts_resolver(self):
        # def conflicts_resolver(self, file_resolver):  
        sp_res, res, related = yield _get_test_vars()
        res.conflict_files = related
        # the default action is to raise an error
        self.assertRaises(NoResolverError, sp_res.conflicts_resolver, res )
        returnValue(None)
 
    #@inlineCallbacks
    def test_process_file_resolver(self):
        # def process_file_resolver(self, file_resolver):
        mock_data = self.data[self._testMethodName]['mock_objects']
        
        agent = MockTransferAgent()
        sp_res = SyncPathResolver(agent)
        # test delete
        for sub_test_name, state in states.items():
            res = object_mocker( mock_objs, mock_data[sub_test_name])
            transfers = sp_res.process_file_resolver(res)
            print transfers

        #returnValue(None)

    def test_migrate_sync(self):
        fail

# Test module methods
 
    def test_resolver_info(self):
        # def _resolver_info(self, file_resolver):
        resolver = MockFileResolver()
        self.assertRaises(NoFilesError, _resolver_info, resolver )
        
        resolver.state = 4
        resolver.related_files = [1,2,3]
        resolver.peer_files = [4,5,6]
        state, sources, dests = _resolver_info( resolver )
        self.assertEqual( 4, state)
        self.assertEqual( [1,2,3], sources)
        self.assertEqual( [4,5,6], dests)

    @inlineCallbacks
    def test_get_file_from(self):
        #def _get_file_from(sync, related)
        my_files = yield MyFile.all()
        s1 = yield SyncPath.find(1)
        s2 = yield SyncPath.find(2)
        s3 = yield SyncPath.find(3)
        s4 = yield SyncPath.find(4)
        
        m1 = _get_file_from(s1, my_files)
        self.assertEquals(m1.sync_path_id, s1.id)
        
        m2 = _get_file_from(s2, my_files)
        self.assertEquals(m2.sync_path_id, s2.id)
        
        m3 = _get_file_from(s3, my_files)
        self.assertEquals(m3, None)

        self.assertRaises(TooManyFilesError,  _get_file_from, s4, my_files )

        returnValue(None)

