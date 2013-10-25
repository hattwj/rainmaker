from rainmaker_app.lib.net import ssl_server, ssl_client, routes

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
    def test_get(self):
        response = yield self.web.get("files/2/parts")
        print response.value()
        print response.responseCode

        # if you have params / headers:
        response = yield self.web.get("files", {'paramone': 'value'}, {'referer': "http://somesite.com"})
        print response.value()
        print response.responseCode
