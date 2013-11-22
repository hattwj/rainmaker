from rainmaker_app.lib.net import ssl_server, ssl_client, routes
from rainmaker_app.lib.util import ExportArray

from rainmaker_app.test.test_helper import *
from rainmaker_app.test.db_helper import *
from rainmaker_app.test.twisted_web_test_utils import DummySite


class FilesResourceTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/net/resources/files_resource_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )
        self.web = DummySite( routes.resources() )

    @inlineCallbacks
    def test_delete(self):
        ''' delete a file record from db'''
        # assert record exists
        my_file = yield MyFile.find(where=['sync_path_id = ? AND path = ?','1', 'g01'], limit = 1) 
        self.assertNotEqual(my_file, None)
        # delete record
        response = yield self.web.delete("syncs/g/files/g01" )
        my_file = yield MyFile.find(where=['sync_path_id = ? AND path = ?','1', 'g01'], limit = 1) 
        self.assertEquals( my_file , None ) 
        self.assertEquals( 204, response.responseCode) 
        # test that repeated delete returns 404 
        response = yield self.web.delete("syncs/g/files/g01" )
        self.assertEquals( 404, response.responseCode) 
         
    @inlineCallbacks
    def test_create(self):
        # create a file
        args = {'file':{'path':'new', 'is_dir': 0}}
        response = yield self.web.post("syncs/g/files", args )
        my_file = yield MyFile.find(where=['sync_path_id = ? AND path = ?','1', 'new'], limit = 1) 
        self.assertEquals( my_file.to_json(), response.value() ) 
        
        # create a duplicate file: should error
        response = yield self.web.post("syncs/g/files", args )
        self.assertEquals( 'Path already exists', response.value() ) 
    
    @inlineCallbacks
    def test_update(self):
        # update a file
        args = {'file':{'path':'new', 'is_dir': 0}}
        response = yield self.web.put("syncs/g/files/g01", args )
        my_file = yield MyFile.find(where=['sync_path_id = ? AND path = ?','1', 'new'], limit = 1) 
        self.assertEquals( my_file.to_json(), response.value() ) 
        self.assertEquals( my_file.id, 1 )
        my_file = yield MyFile.find(where=['sync_path_id = ? AND path = ?','1', 'g01'], limit = 1) 
        self.assertEquals( my_file.id, 2 )
        self.assertEquals( 200, response.responseCode) 
        my_files = yield MyFile.all() 
        
    @inlineCallbacks
    def test_index(self):
        # list files
        response = yield self.web.get("syncs/g/files")
        my_files = yield MyFile.find(where=['sync_path_id = ?','1']) 
        my_files = ExportArray(my_files)
        self.assertEquals( my_files.to_json(), response.value() )
        self.assertEquals( 200, response.responseCode) 
        
        # files index of missing sync
        response = yield self.web.get("syncs/missing/files")
        #self.assertEquals( my_files.to_json(), response.value() )
        self.assertEquals( 404, response.responseCode) 
    
    @inlineCallbacks
    def test_show(self):

        # show file info
        response = yield self.web.get("syncs/g/files/g01")
        my_file = yield MyFile.find(where=['path = ?','g01'], limit = 1)
        self.assertEquals( my_file.to_json(), response.value() )
        self.assertEquals( 200, response.responseCode) 
         
        # missing sync
        response = yield self.web.get("syncs/none/files/2")
        self.assertEquals( 404, response.responseCode) 
        
        # missing file
        response = yield self.web.get("syncs/g/files/none")
        self.assertEquals( 404, response.responseCode)
