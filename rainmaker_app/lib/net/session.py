from os import urandom

from passlib.hash import bcrypt as hashify
from passlib import exc
from twisted.internet import defer

from . commands import ErrAuthRand, ErrAuthSyncPath, ErrAuthInit, ErrAuthFail

class Session(object):
    '''
        Holds server and client connection session variables
        Determines if a connected peer is authenticated
    '''
    ##
    # Class Variables
    ##
    HROUNDS = 12

    ##
    # Class Instance Variables
    ##
    _sync_path = None
    _peer_rand = None
    _peer_pass = None
    _peer_cert = None
    _encrypted_password = None

    def __init__(self, auth):
        self.auth = auth
        self.rand = urandom(500).encode('base-64')
        self.authenticated = False

    def authorizeParams(self):
        print self.sync_path.guid
        return {
            'rand': self.rand,
            'guid': self.sync_path.guid,
            'enc_pass': self.encrypted_password
        }

    def authorize(self, rand, enc_pass):
        self.peer_rand = rand 
        try:
            valid = hashify.verify(self.peer_password, enc_pass)
        except ValueError as e:
            raise ErrAuthFail(repr(e))
        if not valid:
            raise ErrAuthFail('Authorization of peer failed')
        self.authenticated = True
        return {
            'rand': self.rand,
            'enc_pass': self.encrypted_password
        }

    @property
    def encrypted_password(self):
        if self._encrypted_password:
            return self._encrypted_password
        self._encrypted_password = hashify.encrypt(self.local_password, rounds=self.HROUNDS)
        return self._encrypted_password

    @property
    def local_password(self):
        return self.rand + self.auth.cert_str + self.sync_path.password_rw

    @property 
    def peer_password(self):
        return self.peer_rand + self.peer_cert + self.sync_path.password_rw

    # Random string sent from remote
    @property
    def peer_rand(self):
        if not self._peer_rand:
            raise ErrAuthInit('random seed not set')
        return self._peer_rand

    @peer_rand.setter
    def peer_rand(self, val):
        '''
            can only be set once
        '''
        if self._peer_rand:
            raise ErrAuthInit('random seed already set')
        if len(val) < 50:
            raise ErrAuthRand('random value too short')
        self._peer_rand = val
    
    # SyncPath that was selected by peer
    @property
    def sync_path(self):
        if not self._sync_path:
            raise ErrAuthInit('sync not set')
        return self._sync_path

    @sync_path.setter
    def sync_path(self, val):
        '''
            can only be set once
        '''
        if self._sync_path:
            raise ErrAuthInit('sync already set')
        # we tried to set the val to None meaning nothing was found in the database
        if not val:
            raise ErrAuthSyncPath('SyncPath not found')
        self._sync_path = val
    
    # TLS Certificate String from Remote
    @property
    def peer_cert(self):
        if not self._peer_cert:
            raise ErrAuthInit('certificate not set')
        return self._peer_cert

    @peer_cert.setter
    def peer_cert(self, val):
        '''
            can only be set once
        '''
        if self._peer_cert:
            raise ErrAuthInit('certificate already set')
        self._peer_cert = val
    
    # return the parameters used to start the session
    def certParams(self):
        return self.auth.certParams(self.peer_cert)

from .exceptions import AuthRequiredError
def require_secure(func):    
    ''' decorator to require secure connection '''
    def sub_require_secure(self, *args, **kwargs):
        ''' nested func to access func parameters'''
        t = self.transport
        if hasattr(t,'getPeerCertificate') and t.getPeerCertificate():
            # run
            d = func(self, *args, **kwargs)
            return d # string
        else:
            raise AuthRequiredError() 
    return sub_require_secure
