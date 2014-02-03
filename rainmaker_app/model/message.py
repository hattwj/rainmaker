from rainmaker_app.lib.net import cert 
from rainmaker_app.model.common import *

class Message(Base):
    pubkey_id = None
    signature = None
    data = None
    signed_at = None

    MAX_AGE = 2*24*60*60*1000 # 2 days
    MAX_FUTURE = 2*24*60*60*1000 # 2 days in the future 

    BELONGSTO = ['pubkey']
    BEFORE_CREATE = ['set_created_at', 'create_pubkey']
    ATTR_ACCESSIBLE = ['signature','data', 'pubkey_str', 'signed_at']

    @defer.inlineCallbacks
    def create_pubkey(self):
        """ create pubkey if it is not already present """
        pubkey = yield Pubkey.findOrCreate(pubkey_str = self.pubkey_str)
        self.pubkey_id = pubkey.id
        if not self.pubkey_id:
            defer.returnValue(False)
            return
        print "YAY we created a message"

    def sign_with(self, pkey_str):
        """ sign the message with the pkey_str, data and current time """
        self.signature = cert.sign_data( pkey_str, self.sig_data ) 

    def valid_signature(self):
        ''' Check to see if the message has a valid signature '''
        return cert.verify_sign( self.pubkey_str, self.signature, self.sig_data)
    
    @property
    def sig_data(self):
        if not self.signed_at:
            self.signed_at = self.time_now()
        return '%s-%s' % (self.data, self.signed_at)         

def message_validator(message):
    if not message.pubkey_str:
        message.errors.add('pubkey_str', 'missing')

    if not message.data:
        message.errors.add('data', 'missing')
    
    if not message.signature:
        message.errors.add('signature', 'missing')
    
    if not message.signed_at:
        message.errors.add('signed_at', 'missing')
    
    if message.signed_at > message.time_now() + message.MAX_FUTURE:
        message.errors.add('signed_at', 'from future')

    if message.signed_at < message.time_now() - message.MAX_AGE:
        message.errors.add('signed_at', 'too old')

    if not message.errors.isEmpty():
        return 

    try:
        if not message.valid_signature():
            message.errors.add('signature', 'invalid')
    except:
        message.errors.add('pubkey_str', 'invalid')

Message.addValidator( message_validator )
