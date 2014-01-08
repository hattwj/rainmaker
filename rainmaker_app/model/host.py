from hashlib import sha256
from rainmaker_app.model.pubkey import *

class Host(Base):
    BELONGS_TO = ['pubkey']
    BEFORE_CREATE = ['set_created_at', 'set_updated_at']
    BEFORE_UPDATE = ['set_updated_at', 'set_last_seen_at']
    ATTR_ACCESSIBLE = []
    TIMEOUT = 15*60*1000    # mark host as stale when updated_at greater than
    
    last_seen_at = 0

    @property
    def is_stale(self):
        self.time_now() - old.last_seen_at > self.TIMEOUT

    @property
    def get_signature(self):
        return "%s%s%s" % (self.address, self.udp_port, self.tcp_port, self.pubkey.pubkey)

    def set_last_seen_at(self):
        self.last_seen_at = self.time_now()

    @property
    def node_id(self):
        if not self.__node_id:
            self.__node_id = sha256(key).digest()
        return self.__node_id

def host_signature(self):
    ''' Validate the host_signature'''
    pass

def host_attrs(self): 
    if not(__valid_port__(self.udp_port) and __valid_port__(self.tcp_port) ):
        return False

def __valid_port__(port):
    port = int(port)
    if port > 0 or port < 2**16:
        return True
    return False


Host.validatesPresenceOf('address','port', 'pubkey_id')
Host.addValidator(host_attrs)
Host.addValidator(host_signature)

