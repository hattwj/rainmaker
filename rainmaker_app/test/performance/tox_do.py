from twisted.internet import defer, reactor
from rainmaker_app.test import test_helper
from rainmaker_app.test import db_helper
from rainmaker_app.tox import tox_ring, tox_env
from rainmaker_app.conf import initializers

sb = None
pb = None
primary_fired = False

@defer.inlineCallbacks
def setUp():
    global sb
    global pb
    global primary_fired

    #test_helper.clean_temp_dir()
    yield db_helper.initDB(test_helper.db_path)
    tox_html = test_helper.load('test/fixtures/tox_nodes.html', raw=True)
    yield initializers.tox.configure(tox_html=tox_html)
    primary_fired = False
    
    pb = tox_ring.PrimaryBot()
    sb = tox_ring.SyncBot(pb.get_address())
    sb.events.register('tox_search_completed', on_tox_event)
    d = sb.start()
    dd = pb.start()
    yield d
    yield dd
    yield db_helper.tearDownDB()

def on_tox_event(event):
    global sb
    global pb
    global primary_fired
    primary_fired = True
    sb.stop()
    pb.stop()

setUp()
reactor.run()
