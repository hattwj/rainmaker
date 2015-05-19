import os
from rainmaker.tests import test_helper, factory_helper as fh
from rainmaker.main import Application
from rainmaker.db.main import Sync
from rainmaker.tox.main import ToxFactory

def AutoApp(apath):
    user_dir = test_helper.user_dir+str(apath)
    app = Application(user_dir=user_dir)
    sync_path = os.path.join(test_helper.sync_root, 'kitchen_sync'+ str(apath))
    app.fs_log.mkdir(sync_path)
    sync = Sync(path=sync_path)
    app.autorun()
    return app

def setup():
    Application.ToxFactory = MockTox

def tear_down():
    Application.ToxFactory = ToxFactory

def test_simple_workflow():
    print("\n\n")
    app1 = AutoApp('1')
    app2 = AutoApp('2')
    
