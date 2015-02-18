
from rainmaker.db.main import init_db, Sync, SyncFile
from rainmaker.sync_manager import scan_manager

from rainmaker.tests import factory_helper

def test_scan_path():
    session = init_db()
    sync = factory_helper.Sync()
    session.add(sync)
    session.commit()
    factory_helper.Dirs(sync.path, 5)
    factory_helper.Files(sync.path, 5)
    scan_manager.scan(session)
    sync_files = session.query(SyncFile).\
        join(Sync).filter(Sync.id==sync.id).all()
    assert len(sync_files) == 10 
