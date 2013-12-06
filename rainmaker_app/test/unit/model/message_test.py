from rainmaker_app.lib.net import cert
from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

class MessageTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/model/message_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
 
    @inlineCallbacks
    def test_validations(self):
        ''' should validate only signed messages '''
        cert_str, pkey_str = cert.create_cert(512)
        pubkey_str = cert.pkey_str_to_pubkey_str(pkey_str)
        data = 'Hello World'
        m = Message()
        m.signature = cert.sign_data(pkey_str, data) 
        m.pubkey_str = pubkey_str
        m.data = data
        valid = yield m.isValid()
        self.assertEquals(valid, True)
        self.message = m

    @inlineCallbacks
    def test_ability_to_create_pubkey(self):
        yield self.test_validations()
        yield self.message.save()
        self.assertEquals(self.message.errors.isEmpty(), True)
        self.assertEquals(self.message.pubkey_id > 0, True)
