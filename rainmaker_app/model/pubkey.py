from rainmaker_app.model.common import *

class Pubkey(Base):
    HASMANY = ['messages']
    ATTR_ACCESSIBLE = ['pubkey_str']

Pubkey.validatesPresenceOf('pubkey_str')
