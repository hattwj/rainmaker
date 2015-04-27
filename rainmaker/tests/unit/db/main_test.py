from rainmaker.tests import test_helper, factory_helper
from rainmaker.main import Application
from rainmaker.db.main import init_db, HostFile, SyncFile, Sync, \
        Host
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

def test_sync_delete_cascades():
    session = init_db()
    sync = factory_helper.Sync(1)
    sync_file = factory_helper.SyncFile(sync, 1, fake=True, 
            file_size=98765 ,is_dir=False)
    host = factory_helper.Host(sync, 1)
    host_file = factory_helper.HostFile(host, 1, is_dir=False)
    session.add(sync)
    session.commit()
    sync = session.query(Sync).first()
    assert len(sync.hosts) > 0
    assert len(session.query(Host).all()) > 0
    assert len(session.query(SyncFile).all()) > 0
    assert len(session.query(HostFile).all()) > 0
    session.delete(sync)
    assert len(session.query(Sync).all()) == 0
    assert len(session.query(Host).all()) == 0
    assert len(session.query(SyncFile).all()) == 0
    assert len(session.query(HostFile).all()) == 0

