from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.net.cert import *

class CertTest(unittest.TestCase):
    
# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/conflict_manager/file_resolver.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
# Tests 
    def test_create_self_signed_cert(self):
        print create_self_signed_cert()

