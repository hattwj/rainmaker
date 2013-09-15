from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class FileResolverTest(unittest.TestCase):
    
# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()

# Utility Functions
    @inlineCallbacks
    def load_fixture(self, test_name):
        data = load('test/fixtures/db/file_resolver.yml')
        for table, records in data[test_name].iteritems():
            if 'my_file' == table:
                for r in records:
                    yield MyFile(**r).save()
# Tests

    @inlineCallbacks
    def test_deleted(self):
        yield self.load_fixture('test_deleted')

        my_files = yield MyFile.all()
        my_file = my_files.pop()
        file_resolver = FileResolver(my_file)
        file_resolver.compare_with(my_files)
        print file_resolver.related_ids()

