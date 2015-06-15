from time import sleep

from rainmaker.tests import test_helper, factory_helper
from rainmaker.db.main import init_db
from rainmaker.tox import tox_ring, tox_env, main
from rainmaker.net.events import Event


def tox_setup():
    DbConn = init_db()
    tox_html = test_helper.load('fixtures/tox_nodes.html')
    session = DbConn()
    main.init_tox(session, tox_html=tox_html)
    sync = factory_helper.Sync(fake=True)
    session.add(sync)
    session.commit()
    pb = tox_ring.PrimaryBot(DbConn, sync)
    sb = tox_ring.SyncBot(DbConn, sync, primary=pb)
    return pb, sb


def test_basic_auth():
    pb, sb = tox_setup()
    sbsess = sb.sessions.get_session(pb.get_address())
    pbsess = pb.sessions.get_session(sb.get_address())
    vpb = pbsess.get_hash(sbsess.nonce)
    vsb = sbsess.get_hash(pbsess.nonce)
    assert pbsess.authenticate(vsb)
    assert sbsess.authenticate(vpb)

def test_can_find_and_transmit(): 
    
    def _on_primary_found(event):
        _on_primary_found.fired = True
        sb.actions.trigger('handshake', 
                params={'addr': pb.get_address()}, reply=_on_auth)

    def _on_auth(event):
        assert event.status == 'ok'
        sb.send('large_msg', data={'msg':'123456789'*999}, addr=pb.get_address())

    def _on_large_message(event):
        _on_large_message.fired = True
        assert event.val('msg') == '123456789' * 999
        sb.stop()
    
    _on_primary_found.fired = False
    _on_large_message.fired = False

    pb, sb = tox_setup()
    pb.sync_bot = sb
    sb.actions.register('tox_search_completed', _on_primary_found)
    pb.router.register('large_msg', _on_large_message)

    d = sb.start()
    dd = pb.start()
    d.join()
    pb.stop()
    dd.join()
    assert _on_primary_found.fired == True
    assert _on_large_message.fired == True
 
    

