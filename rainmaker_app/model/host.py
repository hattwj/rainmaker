from hashlib import sha256
from rainmaker_app.model.common import *
from rainmaker_app.lib.net.cert import Pubkey
from rainmaker_app import app

class Host(Base):
    ATTR_ACCESSIBLE = ['pubkey_str', 'address', 'tcp_port', 
        'udp_port', 'signature', 'nonce']
    BEFORE_CREATE = ['set_created_at', 'set_updated_at', '__set_last_seen_at__']
    BEFORE_UPDATE = ['set_updated_at', '__set_last_seen_at__']
    TIMEOUT = 15*60*1000    # mark host as stale when updated_at greater than
    last_seen_at = 0
    __pubkey__ = None   # pubkey object
    pubkey_str = None

    @property
    def pubkey(self):
        ''' return pubkey object '''
        if self.__pubkey__:
            return self.__pubkey__
        if not self.pubkey_str:
            raise AttributeError('No pubkey loaded')
        self.__pubkey__ = Pubkey(self.pubkey_str)
        return self.__pubkey__

    @property
    def is_stale(self):
        ''' is the host data old?'''
        # offset timeout for old hosts 
        last_seen_at = self.last_seen_at
        if app.started_at > last_seen_at:
            # old hosts have 5 minutes to respond
            last_seen_at = app.started_at - int(self.TIMEOUT / 3) 
        return self.time_now() - last_seen_at > self.TIMEOUT

    @property
    def signature_data(self):
        if not self.nonce:
            self.nonce = self.time_now()
        return "%s%s%s%s" % (self.address, self.udp_port, self.tcp_port, self.nonce)

    def __set_last_seen_at__(self):
        ''' update last seen at '''
        self.last_seen_at = self.time_now()

    @property
    def node_id(self):
        ''' b64 encoded 32bit hash of pubkey '''
        return self.pubkey.guid
    
    @property
    def signature_data(self):
        return "%s%s%s%s" % (self.address, self.udp_port, self.tcp_port, self.nonce)

    def verify_sig(self):
        ''' verify host data signature '''
        return self.pubkey.verify(self.signature, self.signature_data)

def host_pubkey(self):
    ''' validate pubkey, only if present '''
    if not self.pubkey_str: return True
    if not self.verify_sig():
        self.errors.add('Signature', 'Validation failed')

def validate_ports(self):
    ''' require valid port range '''
    if not __valid_port__(self.tcp_port):
        self.errors.add('tcp_port', 'invalid')
    if not __valid_port__(self.udp_port):
        self.errors.add('udp_port', 'invalid')
    if len(self.errors) > 0:
        return False
    return True

def __valid_port__(port):
    port = int(port)
    if port > 0 and port < 2**16:
        return True
    return False

Host.validatesPresenceOf(
    'address',
    'udp_port', 
    'tcp_port')
Host.addValidator(host_pubkey)
Host.addValidator(validate_ports)
