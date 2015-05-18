import os
from rainmaker.tests import test_helper, factory_helper as fh
from rainmaker.main import Application
from rainmaker.db.main import Sync

def setup_app(apath):
    user_dir = test_helper.user_dir+str(apath)
    app = Application(user_dir=user_dir)
    sync_path = os.path.join(test_helper.sync_root, 'kitchen_sync'+ str(apath))
    app.fs_log.mkdir(sync_path)
    sync = Sync(path=sync_path)
    app.autorun()
    return app

def test_simple_workflow():
    print("\n\n")
    app = setup_app('1')
    app = setup_app('2')
