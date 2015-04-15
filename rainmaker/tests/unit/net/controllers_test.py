from rainmaker.db.main import init_db
from rainmaker.tests.factory_helper import Sync
from rainmaker.tox.tox_ring import ToxBot
from rainmaker.net.controllers import tox_auth_controller


class MockTox(ToxBot):

    def __init__(self, *args, **kwargs):
        super(MockTox, self).__init__(*args, **kwargs)

def do_prep():
    db = init_db()
    primary = MockTox()
    tox1 = MockTox(primary=primary)
    tox2 = MockTox(primary=primary)
    return (db, primary, tox1, tox2)

def test_auth_controller_authenticates():
    def do_auth(event):
        nonce = event.val('nonce')
        passwd_hash = tox2.sessions.get_hash(tox1.get_address(), nonce)
        params = {'pk': tox2.get_address(), 'passwd_hash': passwd_hash}
        tox1.trigger('create_session', 
                params=params, reply=check_auth)  
        do_auth.ran = True

    def check_auth(event):
        assert event.status == 'ok'
        check_auth.ran = True

    check_auth.ran = False
    do_auth.ran = False

    db, primary, tox1, tox2 = do_prep()

    tox_auth_controller(db, tox1)
    args = {'pk': tox2.get_address()}
    tox1.trigger('new_session', params=args, reply=do_auth)

    assert check_auth.ran == True
    assert do_auth.ran == True


    

