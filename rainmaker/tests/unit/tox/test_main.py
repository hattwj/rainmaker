from rainmaker.tests import test_helper
from rainmaker.db.main import init_db
from rainmaker.tox.main import init_tox

def test_can_initialize_tox():
    session = init_db()
    init_tox(session)
