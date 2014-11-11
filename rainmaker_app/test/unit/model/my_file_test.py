from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

class MyFileTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        print 'Running'

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
 
    @inlineCallbacks
    def test_attribute_reset(self):
        ''' no difference between sets '''
        g = yield MyFile(sync_path_id=1, path='ggg').save()
        g.path='aaa'
        g.reset()
        self.assertEqual('ggg', g.path)
    
    def test_ability_to_scan(self):
        new_files = write_many(data_dir) 
        for fpath in new_files:
            mfile = MyFile(sync_path_id=1, path=fpath)
            mfile.scan()
            self.assertEquals(mfile.fhash != None, True)
            self.assertEquals(mfile.scanned_at > 0, True)
