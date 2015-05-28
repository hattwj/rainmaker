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
    def _require_auth(transport, event):
        if not transport.router.auth_strategy:
            raise AuthConfigError('No Strategy defined')
        _func = transport.router.auth_strategy(transport, func)
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
        Sessions for individual client
        - gen challenge per pk
        - gen response per pk, nonce
    '''

    def __init__(self, tox):
        self.valid_fids = set()
        self.valid_pks = set()
        self._store = LStore()
        self._temp_store = LStore(30)
        self.tox = tox
    
    @property
    def pk(self):
        return self.tox.get_address()

    @property
    def secret(self):
        _, secret = self.tox.primary.get_keys()
        return secret

    def get_nonce(self, pk):
        ''' get/generate nonce for client '''
        key = 'nonce:%s' % pk

        def _new_nonce():
            return rand_str(40)

        for nonce in self._temp_store.yget(key, _new_nonce):
            return nonce

    def get_hash(self, pk, nonce):
        ''' get/generate hash to submit for authentication''' 
        key = 'hash:%s%s' % (pk, nonce)
        def _new_hash():
            passwd = '%s%s%s' % (self.secret, self.pk, nonce)
            return bcrypt_sha256.encrypt(passwd)
        for hashed_pass in self._temp_store.yget(key, _new_hash):
            return hashed_pass

    def authenticate(self, pk, _hash):
        '''
            Authenticate client
        '''
        nonce = self.get_nonce(pk)
        passwd = self.secret + pk + nonce
        try:
            valid = bcrypt_sha256.verify(passwd, _hash)
        except ValueError as e:
            valid = False
        if valid and pk not in self.valid_pks: 
            self._store.put(pk, LStore())
            xfid = self.tox.add_friend_norequest(pk)
            self.valid_fids.add(xfid)
            self.valid_pks.add(pk)
        return valid

    def valid_fid(self, fid):
        return fid in self.valid_fids
    
    def valid_pk(self, pk):
        return fid in self.valid_pks
        
    def put(self, pk, key, obj):
        self._store.get(pk).put(key, obj)

    def get(self, pk, key):
        return self._store.get(pk).get(key)
