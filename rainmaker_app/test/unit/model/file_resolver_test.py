from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.model.file_resolver import FileResolver

class FileResolverTest(unittest.TestCase):
    
# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/model/file_resolver.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()

# Tests

    @inlineCallbacks
    def test_deleted_no_conflict(self):
        my_files = yield Difference.between_sync_paths( 1, 2 )
        # test difference expectation
        #self.assertEquals( len(my_files), 2)
        #print my_files
        # process all new files
        while len(my_files) > 0:
            my_file = my_files.pop()
            file_resolver = FileResolver(my_file)
            file_resolver.resolve_against( my_files )
            #last child was deleted
            child = file_resolver.last_child
            self.assertEquals( child.my_file.state, MyFile.DELETED )
            # has parent/child
            parent = file_resolver.first_parent
            
            print parent
            
            #myfd(my_file)
            details(parent)

            self.assertEquals( parent.child, child )
            self.assertEquals( child.parent, parent )
            
            # no conflicts 
            self.assertEquals( 0, len(file_resolver.conflict_files) )
            # prep for next round
            my_files = file_resolver.unrelated_files

def myfd(m):
    print "\n\tid : %s \n\tp : %s\n\tsid : %s\n\tfh : %s\n\tnid : %s" % (m.id, m.path, m.sync_path_id, m.fhash, m.next_id)
    
def details(file_resolver):
    print '####main'
    kv = file_resolver.result()
    for k, v in kv.iteritems():
        print "%s - %s\n" % (k, v)
    print "resolver end\n\n####"
    
    # 
    kv = file_resolver.first_parent.result()
    for k, v in kv.iteritems():
        print "%s - %s\n" % (k, v)
    print "resolver end\n"
