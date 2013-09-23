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
    def test_reset(self):
        ''' no difference between sets '''
        g = yield MyFile(sync_path_id=1, path='ggg').save()
        g.path='aaa'
        g.reset()
        self.assertEqual('ggg', g.path)
    
    @inlineCallbacks
    def load_fixture(self, test_name):
        data = load('test/fixtures/db/my_files.yml')
        for r in data[test_name]['my_file']:
            print r
            yield MyFile(**r).save()


