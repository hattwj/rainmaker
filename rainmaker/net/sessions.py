from rainmaker.net.errors import AuthError, EventError
from rainmaker.net.utils import LStore

def controller_requires_auth(func):
    '''
        Controller decorator
        - All route responders added from func will require authentication
    '''
    def _controller_requires_auth(db, transport):
        transport.router.auth_strategy_on()
        func(db, transport)
        transport.router.auth_strategy_off()
    return _controller_requires_auth

def require_auth(func):
    '''
        Authorization decorator for event responders
    '''
    def _require_auth(event):
        if not event.transport.router.auth_strategy:
            raise AuthConfigError('No Strategy defined')
        _func = event.transport.router.auth_strategy(event.transport, func)
        return _func(event)
    return _require_auth

def tox_auth_strategy(tox, func):
    '''
        Event responder decorator to require auth
        - Passed to EventHandler from tox.router init
        - Authentication and Authorization all in one
    '''
    def _tox_auth_strategy(event):
        try:
            fid = event.val('fid')
        except EventError as e:
            raise AuthError('No fid')
        if not tox.sessions.valid_fid(fid):
            raise AuthError('Not Authenticated')
        tox_permission_strategy(tox, event, fid)
        return func(event)
    return _tox_auth_strategy

def tox_permission_strategy(tox, event, fid):
    '''
        Permission strategy for tox
        - Monitor incoming requests for sync_id references
    '''
    sync_id = event.data.get('sync_id')
    if sync_id: 
        if sync_id != tox.sync.id:
            raise AuthError('Not Permitted')

from passlib.hash import bcrypt_sha256
from rainmaker.utils import rand_str

class ToxSessions(object):
    '''
        Sessions for individual server
        - gen challenge per pk
        - gen response per pk, nonce
    '''

    def __init__(self, tox):
        self.valid_pks = set()
        self._temp_store = LStore(40)
        self.tox = tox
    
    @property
    def secret(self):
        _, secret = self.tox.primary.get_keys()
        return secret[:64]

    @property
    def addr(self):
        return self.tox.get_address()[:64]

    def get_session(self, addr=None, fid=None):
        assert fid is not None or addr is not None
        addr = addr if addr is not None else self.tox.get_client_id(fid)
        addr = addr[:64]
        def _new_session():
            return Session(self.addr, addr, self.secret)
        key = addr
        for session in self._temp_store.yget(key, _new_session):
            return session
    
    def valid_fid(self, fid):
        return self.get_session(self.tox.get_client_id(fid)).valid

NONCE_LEN = 40

class Session():
    '''
        Session for single client
        - recv nonce, send hash = get_hash(peer_nonce)
        - send nonce, recv hash = authenticate(_hash)
        - enc/dec secret + peer_addr + my_nonce
    '''
    def __init__(self, addr, peer_addr, secret):
        self.addr = addr
        self.peer_addr = peer_addr
        self.secret = secret
        self._phash = None
        self.valid = False
        self.nonce = rand_str(40)

    def get_hash(self, peer_nonce):
        if len(str(peer_nonce)) < NONCE_LEN:
            raise AuthError('Nonce too short')
        #if self._phash is None:
        passwd = '%s%s%s' % (self.secret, self.addr, peer_nonce)
        self._phash = bcrypt_sha256.encrypt(passwd)
        return self._phash
     
    def authenticate(self, _hash):
        '''
            Authenticate client
        '''
        passwd = '%s%s%s' % (self.secret, self.peer_addr, self.nonce)

        try:
            self.valid = bcrypt_sha256.verify(passwd, _hash)
        except ValueError as e:
            log.error('Auth Error: from %s' % self.peer_addr)
            self.valid = False
        return self.valid
    
