from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.net.cert import *

class CertTest(unittest.TestCase):
    
# Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/net/cert_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
# Tests 
    def test_create_cert(self):
        cert_str, pkey_str = create_cert(size=512)
        self.assertEquals( len(cert_str)>0, True)
        self.assertEquals( len(pkey_str)>0, True)

        cert, pkey = create_cert(size=512, as_objects=True)

    def test_pkey_to_pem_pubkey(self):
        cert, pkey = create_cert(size=512, as_objects=True)
        pubkey_str = pkey_to_pem_pubkey(pkey)
        print pubkey_str

    def test_create_pubkey_str(self):
        from Crypto.PublicKey import RSA
        cert_str, pkey_str = create_cert(size=512)
        pkey = RSA.importKey(pkey_str) 
        pubkey = pkey.publickey()
        
        # We have created the pubkey
        pubkey_str = pubkey.exportKey()       
        
        # Now use it to encode a message for the private key
        message = 'Hello World!'
        enc_msg = encrypt_RSA(pubkey_str,message)
        dec_msg = decrypt_RSA(pkey_str,enc_msg)
        self.assertEquals(dec_msg, message)


    def test_rsa_encrypt_decrypt(self):
        cert_str, pkey_str = create_cert(size=512)
        message = 'Hello World!'
        enc_msg = encrypt_RSA(pkey_str,message)
        dec_msg = decrypt_RSA(pkey_str,enc_msg)
        self.assertEquals(message, dec_msg)
