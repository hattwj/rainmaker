from rainmaker_app.lib.net import ssl_server, ssl_client, routes

from rainmaker_app.test.test_helper import *
from rainmaker_app.test.db_helper import *
from rainmaker_app.test.twisted_web_test_utils import DummySite

class SSLServerTest(unittest.TestCase):
    def setUp(self):
        self.web = DummySite( routes.resources() )

    @inlineCallbacks
    def test_get(self):
        response = yield self.web.get("files/2")
        print response.value()
        #self.assertEqual(response.value(), "hello")
        # if you have params / headers:
        response = yield self.web.get("files/", {'paramone': 'value'}, {'referer': "http://somesite.com"})
        print response.value()


#class SslServerTest(unittest.TestCase):
#    
## Test Preparation
#    @inlineCallbacks
#    def setUp(self):
#        clean_temp_dir()
#        yield initDB(db_path)
#        self.server = ssl_server.SSLServer()
#        self.server.port = 8000
#        self.server.k_path = k_path
#        self.server.c_path = c_path
#        self.server.start()
#        
#        #self.data = load('test/fixtures/unit/lib/net/ssl_server.yml')
#        #yield load_fixture( 'setup', self.data )
#        #yield load_fixture( self._testMethodName, self.data )
#
#    @inlineCallbacks
#    def tearDown(self):
#        yield tearDownDB()
#        yield self.server.stop()
#    
## Tests
#    @inlineCallbacks 
#    def test_keys(self):
#        client = ssl_client.SSLClient(k_path, c_path)
#        #print dir(client)
#        val = yield client.request('GET','https://localhost:8000/files')
#        print val
