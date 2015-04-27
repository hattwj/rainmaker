
from rainmaker.db.main import init_db
from rainmaker.net.controllers import sync_files_controller, \
    file_parts_controller
from rainmaker.sync_manager import actions
from rainmaker.tox.tox_ring import ToxBot
from rainmaker.tests.factory_helper import SyncRand, HostRand

def startup():
    db = init_db()
    sync = SyncRand()
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
    host = sync.hosts[0]
    tox2 = ToxBot(sync2)
    tox2.sessions.valid_fids.add(1)
    sync_files_controller(db2, tox)
    file_parts_controller(db2, tox)
    actions.sync_with_host(db, host, _fake_send)

