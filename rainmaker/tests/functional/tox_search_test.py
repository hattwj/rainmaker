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
    sb = tox_ring.SyncBot(pb)
    pb.sync_bot = sb
    sb.events.register('tox_search_completed', on_tox_event)
    pb._bootstrap = sb.bootstrap
    d = sb.start()
    dd = pb.start()
    #sleep(40)
    d.join()
    pb.stop()
    dd.join()
    assert status['fired'] ==  True

def test_can_transmit_large_messages(): 
    
    def on_large_message(event):
        status['fired'] = True
        do_large() 
    
    def on_tox_event(event):
        do_large()

    def do_large():
        status['fired'] = True
        status['exp'] += 0.1
        print(status)
        msg = tox_ring.Event('large', bb='b'*int(10*status['exp']))
        pid = sb.get_friendlist()[0]
        sb.send_message(pid, msg.serialize())

    status = {
            'fired': False,
            'exp': 0
        }
    session = init_db()
    tox_html = test_helper.load('fixtures/tox_nodes.html')
    main.init_tox(session, tox_html=tox_html)

    pb = tox_ring.PrimaryBot()
    sb = tox_ring.SyncBot(pb)
    pb.sync_bot = sb
    sb.events.register('tox_search_completed', on_tox_event)
    pb.router.register('large', on_large_message)
    sb.router.register('large', on_large_message)
    d = sb.start()
    dd = pb.start()
    #sleep(40)
    d.join()
    pb.stop()
    dd.join()
    assert status['fired'] ==  True

