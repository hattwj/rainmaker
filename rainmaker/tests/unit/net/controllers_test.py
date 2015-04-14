from rainmaker.db.main import init_db
from rainmaker.tests.factory_helper import Sync
from rainmaker.tox.tox_ring import ToxBase
from rainmaker.net.controllers import tox_auth_controller

def test_auth_controller_denies_auth():
    session = init_db()
    sync = Sync(1)
    tox = ToxBase()
    tox_auth_controller(tox)

