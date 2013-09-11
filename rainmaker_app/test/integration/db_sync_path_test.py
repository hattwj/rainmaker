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
    def test_track_changes(self):
        sync_path = yield SyncPath(root=data_dir).save()
        
        # test finding new files
        paths = write_many(data_dir, 10) 
        paths2 = write_many(data_dir, 10) 
        scan_info = yield sync_path.scan()
        self.validate_sync_totals(scan_info)
        
        self.assertEquals( 20, scan_info['count_new'])
        self.assertEquals( 20, scan_info['count_scanned'])
        
        # test finding deleted files
        for path in paths:
            fs.rm(path)
        scan_info = yield sync_path.scan()
        self.validate_sync_totals(scan_info)
        self.assertEquals( len(paths), scan_info['count_deleted'])

        # test re-created files
        for path in paths:
            fs.write(path, 'aaaaa')
        scan_info = yield sync_path.scan()
        self.validate_sync_totals(scan_info)
        self.assertEquals( 0, scan_info['count_deleted'])
        self.assertEquals( len(paths), scan_info['count_stale'])
      
        # test creating dirs
        dirs = []
        for n in range(0,5):
            cur_dir = os.path.join(data_dir, "sub_%s" % n)
            dirs.append( cur_dir )
            fs.mkdir( cur_dir )
        scan_info = yield sync_path.scan()
        self.validate_sync_totals(scan_info)
        self.assertEquals( len(dirs), scan_info['count_new'])
        
        # test adding and removing dirs at same time
        dirs2 = []
        for n in range(6,10):
            cur_dir = os.path.join(data_dir, "sub_%s" % n)
            dirs2.append( cur_dir )
            fs.mkdir( cur_dir )
        for d in dirs:
            fs.rmdir(d)
        scan_info = yield sync_path.scan()
        self.validate_sync_totals(scan_info)
        self.assertEquals( len(dirs2), scan_info['count_new'])
        self.assertEquals( len(dirs), scan_info['count_deleted'])

        # test re-creating dirs
        for d in dirs:
            fs.mkdir( d )
        scan_info = yield sync_path.scan()
        self.validate_sync_totals(scan_info)
        self.assertEquals( len(dirs), scan_info['count_stale'])
    
    # TODO: Not sure how to test 
    #@inlineCallbacks
    #def test_for_deleted_while_hashing_file(self):
    #    #todo
    #    sync_path = yield SyncPath(root=data_dir).save()
    #    fs.write( os.path.join(data_dir,'large_temp_file'), 'a'*10**8)
    #    reactor.callLater(0, sync_path.scan()) 

    def validate_sync_totals(self, totals):
        found = totals['count_new'] + totals['count_no_change'] +\
            totals['count_stale']
        calc = totals['count_scanned']
        self.assertEquals(calc, found)
