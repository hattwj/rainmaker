from rainmaker.net.errors import AuthError, EventError
from rainmaker.net.utils import LStore

def controller_requires_auth(func):
    '''
        Controller decorator
        - All route responders added from func will require authentication
    '''
    def _wrapper(db, transport):
        transport.router.auth_strategy_on()
        func(db, transport)
        transport.router.auth_strategy_off()
    return _wrapper

def require_auth(strategy='tox'):
    strategy = tox_auth_strategy
    def _wrapper(_func):
        print(_func)
        def _swrap(tox, event):
            func = strategy(tox, _func)
            func(tox, event)
        return _swrap
    return _wrapper

def tox_auth_strategy(tox, func):
    '''
        Event responder decorator to require auth
        - Passed to EventHandler from tox.router init
        - Authentication and Authorization all in one
    '''
    def _wrapper(event):
        try:
            fid = event.val('fid')
        except EventError as e:
            raise AuthError('No fid')
        if not tox.sessions.valid_fid(fid):
            raise AuthError('Not Authenticated')
        tox_permission_strategy(tox, event, fid)
        return func(event)
    return _wrapper

def tox_permission_strategy(tox, event, fid):
    sync_id = event.data.get('sync_id')
    host_id = event.data.get('host_id')
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
        self._sess = LStore(30)
        _, self.secret = tox.primary.get_keys()
        self.pk = tox.get_address()
        self.tox = tox

    def get_nonce(self, pk):
        ''' get/generate nonce for client '''
        key = 'nonce:%s' % pk

        def _new_nonce():
            return rand_str(40)

        for nonce in self._sess.yget(key, _new_nonce):
            return nonce

    def get_hash(self, pk, nonce):
        ''' get/generate hash to submit for authentication''' 
        key = 'hash:%s%s' % (pk, nonce)
        def _new_hash():
            passwd = '%s%s%s' % (self.secret, self.pk, nonce)
            return bcrypt_sha256.encrypt(passwd)
        for hashed_pass in self._sess.yget(key, _new_hash):
            return hashed_pass

    def authenticate(self, pk, _hash):
        '''
            Authenticate client
        '''
        nonce = self.get_nonce(pk)
        passwd = self.secret + pk + nonce
        valid = bcrypt_sha256.verify(passwd, _hash)
        if valid and pk not in self.valid_pks: 
            xfid = self.tox.add_friend_norequest(pk)
            self.valid_fids.add(xfid)
            self.valid_pks.add(pk)
        return valid

    def valid_fid(self, fid):
        return fid in self.valid_fids
    
    def valid_pk(self, pk):
        return fid in self.valid_pks
        
class Ability(object):
    
    def __init__(self):
        self.sync_ids = set()
        self.host_ids = set()

    def can(self, event, action, sync_id=None, host_id=None):
        if sync_id:
            return sync_id in self.sync_ids 
        if host_id:
            return host_id in self.host_ids 
        return None
        
        
