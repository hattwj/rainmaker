from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.net import cert
cert_str, pkey_str = cert.create_cert(512)
pubkey_str = cert.pkey_str_to_pubkey_str(pkey_str)

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
 
    def create_message(self):
        ''' should validate only signed messages '''
        data = 'Hello World'
        message = Message()
        message.pubkey_str = pubkey_str
        message.data = data
        self.message = message

    @inlineCallbacks
    def test_ability_to_create_pubkey(self): 
        self.create_message()
        self.message.sign_with(pkey_str)
        yield self.message.save()
        self.assertEquals(self.message.errors.isEmpty(), True)
        self.assertEquals(self.message.pubkey_id > 0, True)
    
    def test_signed_at_validation(self):
        self.create_message()

        sometime = self.message.time_now()
        valid = yield do_validate_signed_at(self.message, sometime)
        self.assertEquals(valid,True)

        # 50 sec within being too old
        sometime = self.message.time_now() - (self.message.MAX_AGE - 50000 )
        valid = yield do_validate_signed_at(self.message, sometime)
        self.assertEquals(valid,True)

        # Too old for 50 seconds already
        sometime = self.message.time_now() - (self.message.MAX_AGE + 50000 )
        valid = yield do_validate_signed_at(self.message, sometime)
        self.assertEquals(valid,False)

        # Almost Too much future
        sometime = self.message.time_now() + (self.message.MAX_FUTURE - 50000 )
        valid = yield do_validate_signed_at(self.message, sometime)
        self.assertEquals(valid,True)

        # Too much future
        sometime = self.message.time_now() + (self.message.MAX_FUTURE + 50000 )
        valid = yield do_validate_signed_at(self.message, sometime)
        self.assertEquals(valid,False)
        

@inlineCallbacks
def do_validate_signed_at(message, sometime):
    # Test signature
    message.signed_at = sometime
    message.sign_with(pkey_str)
    valid = yield message.isValid()
    returnValue(valid)
        
