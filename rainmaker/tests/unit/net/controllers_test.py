from nose.tools import assert_raises

from rainmaker.db.main import init_db
from rainmaker.tests.factory_helper import Sync, SyncFile
from rainmaker.tox.tox_ring import ToxBot
from rainmaker.net.errors import AuthError
from rainmaker.net.controllers import tox_auth_controller, utils_controller, \
        sync_files_controller, file_parts_controller

class MockTox(ToxBot):
    ''' Tox Object '''
    def __init__(self, *args, **kwargs):
        super(MockTox, self).__init__(*args, **kwargs)

def do_prep():
    ''' Gen variables for test '''
    db = init_db()
    sync = Sync(fake=True)
    db.add(sync)
    db.commit()
    primary = MockTox(sync)
    tox1 = MockTox(sync, primary=primary)
    tox2 = MockTox(sync, primary=primary)
    return (db, primary, sync, tox1, tox2)

def auto_auth(db, tox1, tox2, twice=True):
    ''' Auth two tox against each other '''
    def _do_auth(event):
        nonce = event.val('nonce')
        passwd_hash = tox2.sessions.get_hash(tox1.get_address(), nonce)
        params = {'pk': tox2.get_address(), 'passwd_hash': passwd_hash}
        tox1.trigger('create_session', 
                params=params, reply=_check_auth)  
        _do_auth.ran = True

    def _check_auth(event):
        assert event.status == 'ok'
        _check_auth.ran = True

    _check_auth.ran = False
    _do_auth.ran = False
    
    tox_auth_controller(db, tox1)
    args = {'pk': tox2.get_address()}
    tox1.trigger('new_session', params=args, reply=_do_auth)

    assert _check_auth.ran == True
    assert _do_auth.ran == True
    assert len(tox1.get_friendlist()) == 1
    
    if twice:
        auto_auth(db, tox2, tox1, twice=False)

def sim_send(tox1, tox2, cmd, params, func):
    def _reply(event):
        _reply.ran = True
        func(event)
    _reply.ran = False
    pk = tox2.get_address()
    params['fid'] = 0
    tox1.trigger(cmd, params=params, reply=_reply)
    assert _reply.ran == True

def test_auth_controller_authenticates():
    db, primary, sync, tox1, tox2 = do_prep()
    auto_auth(db, tox1, tox2)
    
def test_utils_controller_can_ping_pong():
    def _recv_pong(event):
        _recv_pong.ran = True
        assert event.status == 'pong'
    _recv_pong.ran = False
    db, primary, sync, tox1, tox2 = do_prep()
    utils_controller(db, tox1)
    tox1.trigger('ping', reply=_recv_pong)
    assert _recv_pong.ran == True

def test_sync_files_controller_can_list_and_get():
    def _recv_list(event):
        sync_files = event.val('sync_files')
        print(event)
        if len(sync_files) > 0 and _recv_list.page < 10:
            params = {'since': 0, 'page': _recv_list.page + 1}
            _recv_list.page += 1
            sim_send(tox1, tox2, 'list_sync_files', params, _recv_list)

    def _recv_get(event):
        print(event)
        assert event.val('id') == fsfid
    
    _recv_list.page = 1 
    db, primary, sync, tox1, tox2 = do_prep()
    sync_files = SyncFile(sync, 1000, fake=True, is_dir=False) 
    db.add(sync)
    db.commit()
    fsfid = sync_files[0].id
    sync_files_controller(db, tox1)
    assert_raises(AuthError, sim_send, tox1, tox2, 'list_sync_files', {}, _recv_list)
    assert_raises(AuthError, sim_send, tox1, tox2, 'get_sync_file', {}, _recv_get)
    auto_auth(db, tox1, tox2)
    sim_send(tox1, tox2, 'list_sync_files', {}, _recv_list)
    assert _recv_list.page == 5


