import os
from rainmaker.tests import test_helper, factory_helper as fh
from rainmaker.main import Application
from rainmaker.db.main import Sync
from rainmaker.tox import tox_ring

def AutoApp(apath, **kwargs):
    user_dir = test_helper.user_dir+str(apath)
    sync_path = os.path.join(test_helper.sync_root, 'kitchen_sync'+ str(apath))
    kwargs['user_dir'] = user_dir
    app = Application(**kwargs)
    app.fs_log.mkdir(sync_path)
    sync = fh.SyncRand(path=sync_path, fake=False)
    app.autorun()
    app.db.add(sync)
    app.db.commit()
    app.sync_manager.start()
    return app

def setup():
    pass
    #tox_ring._DefaultBot = tox_ring.DefaultBot
    #tox_ring.DefaultBot = MockTox

def tear_down():
    pass
    #test_helper.clean_temp_dir()
    #tox_ring.DefaultBot = tox_ring._DefaultBot

def test_simple_workflow():
    print("\n\n")
    app1 = AutoApp('1', device_name='app1')
    app2 = AutoApp('2', device_name='app2')
    
