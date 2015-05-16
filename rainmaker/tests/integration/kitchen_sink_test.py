import os
from rainmaker.tests import test_helper
from rainmaker.main import Application

def test_simple_workflow():
    Application.start_sync = False
    Application.tasks.autorun()
    sync_path = os.path.join(test_helper.sync_root, 'kitchen_sync')
    Application.tasks.create_sync(sync_path)
