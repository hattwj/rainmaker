from rainmaker_app.lib.net import ssl_server, ssl_client, routes
from rainmaker_app.lib.util import ExportArray

from rainmaker_app.test.test_helper import *
from rainmaker_app.test.db_helper import *
from rainmaker_app.test.twisted_web_test_utils import DummySite

class SyncPathsResourceTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/net/resources/sync_paths_resource_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )
        self.web = DummySite( routes.resources() )
    
    @inlineCallbacks
    def test_index(self):
        # show all syncs info
        response = yield self.web.get("syncs")
        sync_paths = yield SyncPath.all()
        sync_paths = ExportArray(sync_paths)
        self.assertEquals( sync_paths.to_json(), response.value() )
        self.assertEquals( 200, response.responseCode) 
   
    @inlineCallbacks
    def test_update(self):
        # verify fixture
        sync_path = yield SyncPath.find(where=['guid = ?','some_guid'], limit = 1)
        self.assertEquals( sync_path.root, 'old_root' )
        # verify update
        args = {'sync_path' : {'guid':'new_root'} }
        response = yield self.web.put("syncs/some_guid", args )
        sync_path = yield SyncPath.find(where=['guid = ?','some_guid'], limit = 1)
        self.assertEquals( sync_path.to_json(), response.value() )
        self.assertEquals( sync_path.root, 'new_root' )
        self.assertEquals( 200, response.responseCode)


    @inlineCallbacks
    def test_show(self):
        # show sync info
        response = yield self.web.get("syncs/some_guid")
        sync_path = yield SyncPath.find(where=['guid = ?','some_guid'], limit = 1)
        self.assertEquals( sync_path.to_json(), response.value() )
        self.assertEquals( 200, response.responseCode) 
          
        # missing sync_path guid
        response = yield self.web.get("syncs/non_existant")
        self.assertEquals( 404, response.responseCode)

