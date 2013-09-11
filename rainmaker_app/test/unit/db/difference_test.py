from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class DifferenceTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        print 'Running'

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()

    @inlineCallbacks
    def test_no_conflict(self):
        ''' no difference between sets '''
        yield self.load_fixture('no_conflict')
        g = yield Difference.compare(1, 2)
        self.assertEquals( g, [] )
    
    @inlineCallbacks
    def test_deleted(self):
        yield self.load_fixture('deleted')
        g = yield Difference.resolve(1, 2)
        self.assertEquals( len(g), 2)

        print g
        #gg = yield MyFile.all()
        #print gg

    @inlineCallbacks
    def load_fixture(self, test_name):
        data = load('test/fixtures/db/differences.yml')
        
        for r in data['my_file'][test_name]:
            yield MyFile(**r).save()

