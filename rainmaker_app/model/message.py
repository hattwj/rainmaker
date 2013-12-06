from rainmaker_app.lib.net import cert 
from rainmaker_app.model.pubkey import *

class Message(Base):
    pubkey_id = None
    digest = None
    message = None
    BELONGSTO = ['pubkey']
    BEFORE_CREATE = ['set_created_at', 'create_pubkey']
    ATTR_ACCESSIBLE = ['digest','message', 'pubkey_str']

    @defer.inlineCallbacks
    def create_pubkey(self):
        """ create pubkey if it is not already present """
        pubkey = yield Pubkey.findOrCreate(pubkey_str = self.pubkey_str)
        self.pubkey_id = pubkey.id
        if not self.pubkey_id:
            defer.returnValue(False)

def message_validator(message):
    if not message.pubkey_str:
        message.errors.add('pubkey', 'missing')

    if not message.data:
        message.errors.add('data', 'missing')
    
    if not message.signature:
        message.errors.add('signature', 'missing')
    
    if not message.errors.isEmpty():
        return 
    
    try:
        if not cert.verify_sign( message.pubkey_str, message.signature, message.data):
            message.errors.add('signature','invalid')
    except:
        message.errors.add('pubkey_str','invalid')

Message.addValidator( message_validator )
