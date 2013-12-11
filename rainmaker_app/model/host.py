from rainmaker_app.model.pubkey import *

class Host(Base):
    BELONGSTO = ['authorization']
    BEFORE_CREATE = ['set_created_at']

#Host.validatesPresenceOf('address', 'port', 'authorization_id')
