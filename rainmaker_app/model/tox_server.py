from rainmaker_app.model.common import *
from rainmaker_app.lib.net.cert import Pubkey
from rainmaker_app import app

class ToxServer(Base):
    pass

ToxServer.validatesPresenceOf(
    'ipv4',
    'port', 
    'pubkey')
