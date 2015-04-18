from nose.tools import assert_raises
from rainmaker.tox.tox_ring import ToxBot
from rainmaker.net.events import Event
from rainmaker.net.sessions import ToxSessions, AuthError, require_auth
from rainmaker.db.main import init_db

class MockTox(ToxBot):
    def __init__(self, primary=None):
        super(MockTox, self).__init__(None, primary=primary)
    

def test_session_will_authenticate_and_enforce_auth():
    
    
    tparent = MockTox()
    tmox1 = MockTox(primary=tparent)
    tmox2 = MockTox(primary=tparent)
    tsess1 = tmox1.sessions
    tsess2 = tmox2.sessions
    
    @require_auth
    def func_requiring_auth(event):
       return True
    pk1 = tmox1.get_address()
    pk2 = tmox2.get_address()
    e = Event('', {'fid': 1}, source=tmox1)
    assert_raises(AuthError, func_requiring_auth, tmox1, e)
    nonce = tsess1.get_nonce(pk2)
    chash = tsess2.get_hash(pk1, nonce)
    assert tsess1.authenticate(pk2, 'bad_hash') == False
    assert tsess1.authenticate(pk2, chash) == True
    tsess1.valid_fids.add(1)
    assert func_requiring_auth(tmox1, e) == True

