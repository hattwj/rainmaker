from rainmaker.net.errors import AuthError, EventError
from rainmaker.net.utils import LStore
 
def require_auth(func):
    '''
        Event responder decorator to require auth
    '''
    def wrapper(self, event):
        try:
            fid = event.val('fid')
        except EventError as e:
            raise AuthError('No fid')
        if not self.sessions.valid_fid(fid):
            raise AuthError('Not Authorized')
        return func(self, event)
    return wrapper


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

        def new_nonce():
            return rand_str(40)

        for nonce in self._sess.yget(key, new_nonce):
            return nonce

    def get_hash(self, pk, nonce):
        ''' get/generate hash to submit for authentication''' 
        key = 'hash:%s%s' % (pk, nonce)
        def new_hash():
            passwd = '%s%s%s' % (self.secret, self.pk, nonce)
            return bcrypt_sha256.encrypt(passwd)
        for chash in self._sess.yget(key, new_hash):
            return chash

    def authenticate(self, pk, _hash):
        nonce = self.get_nonce(pk)
        passwd = self.secret + pk + nonce
        valid = bcrypt_sha256.verify(passwd, _hash)
        return valid

    def valid_fid(self, fid):
        return fid in self.valid_fids
    
    def valid_pk(self, pk):
        return fid in self.valid_pks
    
