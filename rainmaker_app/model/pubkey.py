from rainmaker_app.model.common import *

class Pubkey(Base):
    ATTR_ACCESSIBLE = ['pubkey_str']

Pubkey.validatesPresenceOf('pubkey_str')
