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
    tox_servers = fh.ToxServers(app.db)
    [app.db.add(ts) for ts in tox_servers]
    sync = fh.SyncRand(path=sync_path, fake=False)
    app.db.add(sync)
    app.db.commit()
    return app

def setup():
    pass

def tear_down():
    pass
    #test_helper.clean_temp_dir()
from time import sleep
def test_simple_workflow():
    print("\n\n")
    app1 = AutoApp('app1')
    app1.start()
    while True:
        sleep(0.1)
    #app2 = AutoApp('2', device_name='app2')
    #app1.sync_manager.syncs[0].primary_bot.
