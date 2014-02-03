from hashlib import sha256

from rainmaker_app.model.common import Base

class Pubkey(Base):
    ATTR_ACCESSIBLE = ['pubkey_str']
    __guid__ = None 

    @property
    def guid(self):
        if self.__guid__: return self.__guid__
        # 32 byte binary/str digest of pubkey
        self.__guid__ = sha256(self.pubkey_str).digest()
        return self.__guid__

from Crypto.PublicKey import RSA  
def __validate_pubkey__(self):
    ''' Ensure that we can instantiate pubkey '''
    rsakey = RSA.importKey(self.pubkey_str)
    return True
    

Pubkey.validatesPresenceOf('pubkey_str')
