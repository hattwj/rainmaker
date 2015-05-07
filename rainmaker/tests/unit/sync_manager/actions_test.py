
from rainmaker.db import main
from rainmaker.net.controllers import sync_files_controller
from rainmaker.sync_manager import actions
from rainmaker.tox.tox_ring import ToxBot
from rainmaker.tests.factory_helper import SyncRand, Host

def startup():
    db = main.init_db()
    sync = SyncRand()
    Host(sync, 1)
    db.add(sync)
    db.commit()
    return db, sync

def test_action_sync_with_host():
    def _fake_send(cmd, params=None, reply=None):
        params = {} if not params else params
        params['fid'] = 1
        tox2.trigger(cmd, params, reply=reply)
    db, sync = startup()
    db2, sync2 = startup()
    tox2 = ToxBot(sync2)
    tox2.sessions.valid_fids.add(1)
    sync_files_controller(db2, tox2)
    actions.sync_with_host(db, sync.hosts[0], _fake_send)
    hf1count = db.query(main.HostFile).count()
    sf2count = db2.query(main.SyncFile).count()
    assert hf1count == sf2count
