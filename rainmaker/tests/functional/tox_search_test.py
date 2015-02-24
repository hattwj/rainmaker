from time import sleep

from rainmaker.tests import test_helper
from rainmaker.db.main import init_db
from rainmaker.tox import tox_ring, tox_env, main


def test_can_find_primary_node(): 
    
    def on_tox_event(event):
        status['fired'] = True
        sb.stop()

    status = {'fired': False}
    session = init_db()
    tox_html = test_helper.load('fixtures/tox_nodes.html')
    main.init_tox(session, tox_html=tox_html)

    pb = tox_ring.PrimaryBot()
    sb = tox_ring.SyncBot(pb.get_address())
    sb.events.register('tox_search_completed', on_tox_event)
    d = sb.start()
    dd = pb.start()
    #sleep(40)
    d.join()
    pb.stop()
    assert status['fired'] ==  True

