from hashlib import sha256
from twisted.internet  import defer, ssl
from rainmaker_app.model.common import *
from rainmaker_app.lib.net.cert import create_cert, pkey_str_to_pubkey_str, \
    encrypt_RSA, decrypt_RSA, sign_data, verify_sign

class Authorization(Base):
    BELONGSTO = ['sync_path','pubkey']
    BEFORE_SAVE = ['__create_pubkey__']
    FIRST_INIT = ['__generate_pkey__']
    ATTR_ACCESSIBLE = ['key_size', 'create_pubkey']
    key_size = 2048
    create_pubkey = False
    __guid__ = None

    def private_cert(self):
        return ssl.PrivateCertificate.loadPEM(self.pk_str+self.cert_str)
        
    def certificate(self):
        return ssl.Certificate.loadPEM(self.cert_str)

    def certParams(self, for_server=False):
        return paramify( self.private_cert(), self.certificate() )
    
    def __create_pubkey__(self):
        if self.create_pubkey==True:
            Pubkey(pubkey_str=self.pubkey_str).save()
        return True

    def __generate_pkey__(self):
        ''' Create pkey/pubkey/certificate'''
        self.cert_str, self.pk_str = create_cert(int(self.key_size))
        self.pubkey_str = pkey_str_to_pubkey_str(self.pk_str)
        return True

    def encrypt(self, msg):
        return encrypt_RSA(self.pubkey_str, msg)

    def decrypt(self, msg):
        return decrypt_RSA(self.pk_str, msg)
    
    def sign(self, msg):
        if not self.pk_str:
            raise AttributeError('no pkey')
        return sign_data(self.pk_str, msg)

    def verify(self, msg):
        return verify_sign(self.pubkey_str, msg)

    @property
    def guid(self):
        if self.__guid__: return self.__guid__
        # 32 byte binary/str digest of pubkey
        self.__guid__ = sha256(self.pubkey_str).digest()
        return self.__guid__

def paramify( private_cert, *certs):
    return {
        'tls_localCertificate': private_cert,
        'tls_verifyAuthorities': certs
    }

