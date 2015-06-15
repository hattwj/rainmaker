import os
from rainmaker.tests import test_helper, factory_helper as fh
from rainmaker.main import Application
from rainmaker.db.main import Sync
from rainmaker.tox import tox_ring

def AutoApp(apath, **kwargs):
    user_dir = os.path.join(test_helper.user_dir, str(apath))
    sync_path = os.path.join(test_helper.sync_root, 'kitchen_sync_'+ str(apath))
    kwargs['user_dir'] = user_dir
    kwargs['device_name'] = apath
    app = Application(**kwargs)
    app.fs_log.mkdir(sync_path)
    app.init()
    app.init_tox(tox_html=test_helper.load('fixtures/tox_nodes.html'))
    fh.ToxServers(app.db)
    sync = fh.SyncRand(path=sync_path, fake=False)
    app.db.add(sync)
    app.db.commit()
    
    app.sync_manager.add_sync(sync)
    
    return app

from time import sleep
def test_simple_workflow():
    print("\n\n")
    app1 = AutoApp('app1')
    app2 = AutoApp('app2')

    sm1 = app1.sync_manager.syncs[0]
    sm2 = app2.sync_manager.syncs[0]

    tpb = app1.sync_manager.syncs[0].tox_manager.primary_bot.save()
    app2.sync_manager.syncs[0].tox_manager.primary_bot.load(tpb)
    print(sm1.tox_manager.sync_bot.get_address())
    print(sm2.tox_manager.sync_bot.get_address())
    print(sm1.tox_manager.primary_bot.get_address())
    print(sm2.tox_manager.primary_bot.get_address())
    sm1.start(start_primary=True)
    sm2.start()
    while True:
        sleep(0.1)

