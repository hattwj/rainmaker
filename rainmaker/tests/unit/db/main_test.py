from rainmaker.tests import test_helper, factory_helper
from rainmaker.main import Application
from rainmaker.db.main import init_db, HostFile, SyncFile 
from rainmaker.db import main

def test_db_init():
    init_db()

def test_sync_file_version_init():
    init_db()
    assert SyncFile(version=5).version == 5
    
def test_rain_base_before_changes():
    session = init_db()
    sync = factory_helper.Sync(1)
    sync_file = factory_helper.SyncFile(sync, 1)
    assert sync_file.before_changes()['sync_id'] == None

def test_sqlalchemy_property_assignment():
    sf = HostFile()
    sf.vers = [{'version': 0, 'file_size':5}]
    assert sf.vers[0].file_size == 5
    sf = SyncFile()
    sf.vers = [{'version': 0, 'file_size':5}]
    assert sf.vers[0].file_size == 5
