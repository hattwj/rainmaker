from rainmaker.tests import test_helper
from rainmaker.tox import tox_updater

def test_can_parse_tox_html(): 
    tox_html = test_helper.load('fixtures/tox_nodes.html')
    servers = tox_updater.fetch(tox_html)
    assert len(servers) > 0

