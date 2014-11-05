from hashlib import sha256
from base64 import b64encode
from twisted.internet  import defer, ssl
from rainmaker_app.lib.util import assign_attrs
from rainmaker_app.lib.net.cert import create_cert, pkey_str_to_pubkey_str, \
    encrypt_RSA, decrypt_RSA, sign_data, verify_sign, Pubkey, paramify

class EphemeralAuth(object):
    key_size = 2048
    create_pubkey = False
    __guid__ = None
    __pubkey__ = None    
    
    def __init__(self, **kwargs):
        assign_attrs(self, **kwargs)
        self.__generate_pkey__()

    @property
    def pubkey(self):
        if self.__pubkey__:
            return self.__pubkey__
        self.__pubkey__ = Pubkey(self.pubkey_str)
        return self.__pubkey__

    def private_cert(self):
        return ssl.PrivateCertificate.loadPEM(self.pk_str+self.cert_str)
        
    def certificate(self):
        return ssl.Certificate.loadPEM(self.cert_str)

    def certParams(self, cert_str):
        peer_cert = ssl.Certificate.loadPEM(cert_str)
        return paramify( self.private_cert(), peer_cert )
        # only trust our own cert(should fail)    
        #return paramify( self.private_cert(), self.certificate())
        
    def __generate_pkey__(self):
        ''' Create pkey/pubkey/certificate'''
        self.cert_str, self.pk_str = create_cert(int(self.key_size))
        self.pubkey_str = pkey_str_to_pubkey_str(self.pk_str)
        return True

    @property
    def guid(self):
        if self.__guid__: return self.__guid__
        # 32 byte binary/str digest of pubkey
        self.__guid__ = sha256(self.pubkey_str).digest()
        return self.__guid__ 

