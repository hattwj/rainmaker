from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.conflict_manager.sync_path_resolver import \
    SyncPathResolver, _get_file_from, _resolver_info, TooManyFilesError, \
    NoActionError, NoConflictsResolverError, NoFilesError
from rainmaker_app.lib.conflict_manager.file_resolver import FileResolver

# Mock classes and helper functions

class MockFileResolver(object):
    
    def __init__(self, **kwargs):
        #FileResolver._init_properties(self,MyFile(sync_path_id=1))
        self.last_child = self
        for k, v in kwargs.items():
            setattr(self, k, v)

class MockTransferAgent(object):
    
    def create(self, sync_path, my_file):
        return 'create: %s-%s from %s' % (sync_path.id, my_file.path, my_file.sync_path_id)

    def update(self, sync_path, my_file):
        return 'update: %s-%s from %s' % (sync_path.id, my_file.path, my_file.sync_path_id)

    def delete(self, sync_path, my_file):
        return 'delete: %s-%s' % (sync_path.id, my_file.path)
    
    def move(self, my_file, path):
        return 'move: %s-%s to %s-%s' % (my_file.sync_path_id, my_file.path, my_file.sync_path_id, path)

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

    # Tests class instance methods
    def test_init(self):
        # def __init__(self, transfer_agent):
        x = MockTransferAgent()
        y = SyncPathResolver(x)
    
    def test_conflicts_resolver(self):
        # def conflicts_resolver(self, file_resolver):   
        res = MockFileResolver(
            my_file=MyFile(path='a',sync_path_id=1),
            peer_files=[],
            conflict_files = [
                MyFile(path='a',sync_path_id=1),
                MyFile(path='a',sync_path_id=2)
            ],
            sync_paths=[SyncPath(id=1), SyncPath(id=2)],
            related_files=[],
            state=FileResolver.CONFLICT
        )
        sp_res = SyncPathResolver(MockTransferAgent())
        # the default action is to raise an error
        self.assertRaises(NoConflictsResolverError, sp_res.conflicts_resolver, res )
 
    #@inlineCallbacks
    def test_process_file_resolver_new_file(self):
        # def process_file_resolver(self, file_resolver):
        res = MockFileResolver(
            my_file=MyFile(path='a',sync_path_id=1),
            peer_files=[
                MyFile(path='a',sync_path_id=1)
            ],
            sync_paths=[SyncPath(id=1), SyncPath(id=2)],
            conflict_files=[],
            related_files=[],
            state=FileResolver.NEW
        )
        sp_res = SyncPathResolver(MockTransferAgent())
        t_arr = sp_res.process_file_resolver(res)
        self.assertEquals( 1, len(t_arr))
        self.assertEquals( t_arr[0], 'create: 2-a from 1')
    
    def test_process_file_resolver_modified_file(self):
        # def process_file_resolver(self, file_resolver):
        res = MockFileResolver(
            my_file=MyFile(path='a',sync_path_id=1),
            peer_files=[
                MyFile(path='a',sync_path_id=1)
            ],
            sync_paths=[SyncPath(id=1), SyncPath(id=2)],
            conflict_files=[],
            related_files=[MyFile(path='a', sync_path_id=2)],
            state=FileResolver.MODIFIED
        )
        sp_res = SyncPathResolver(MockTransferAgent())
        t_arr = sp_res.process_file_resolver(res)
        self.assertEquals( 1, len(t_arr))
        self.assertEquals( t_arr[0], 'update: 2-a from 1')
    
    def test_process_file_resolver_moved_file(self):
        # def process_file_resolver(self, file_resolver):
        res = MockFileResolver(
            my_file=MyFile(path='b',sync_path_id=1),
            peer_files=[
                MyFile(path='b',sync_path_id=1)
            ],
            sync_paths=[SyncPath(id=1), SyncPath(id=2)],
            conflict_files=[],
            related_files=[MyFile(path='a', sync_path_id=2)],
            state=FileResolver.MOVED
        )
        sp_res = SyncPathResolver(MockTransferAgent())
        t_arr = sp_res.process_file_resolver(res)
        self.assertEquals( 1, len(t_arr))
        self.assertEquals( t_arr[0], 'move: 2-a to 2-b')
    
    def test_process_file_resolver_deleted_file(self):
        # def process_file_resolver(self, file_resolver):
        res = MockFileResolver(
            my_file=MyFile(path='a',sync_path_id=1),
            peer_files=[
                MyFile(path='a',sync_path_id=1)
            ],
            sync_paths=[SyncPath(id=1), SyncPath(id=2)],
            conflict_files=[],
            related_files=[MyFile(path='a', sync_path_id=2)],
            state=FileResolver.DELETED
        )
        sp_res = SyncPathResolver(MockTransferAgent())
        t_arr = sp_res.process_file_resolver(res)
        self.assertEquals( 1, len(t_arr))
        self.assertEquals( t_arr[0], 'delete: 2-a')
    
    ## not tested because this is tested by test_process_file_resolver_xxx series
    #def test_migrate_sync(self):
    #    fail

# Test module methods
 
    def test_resolver_info(self):
        # def _resolver_info(self, file_resolver):
        res = MockFileResolver(peer_files=[])
        self.assertRaises(NoFilesError, _resolver_info, res )
        res = MockFileResolver(
            state = 4,
            related_files = [1,2,3],
            peer_files = [4,5,6]
        )
        state, sources, dests = _resolver_info( res )
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

