from rainmaker.tests import test_helper
from rainmaker.db.main import init_db
from rainmaker.tox.main import init_tox

def test_can_initialize_tox():
    session = init_db()
    tox_html = test_helper.load('fixtures/tox_nodes.html')
    init_tox(session, tox_html=tox_html)
