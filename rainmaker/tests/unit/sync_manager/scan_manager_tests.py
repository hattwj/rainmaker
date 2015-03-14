from rainmaker.db.main import init_db, Sync, SyncFile
from rainmaker.sync_manager import scan_manager
from rainmaker.file_system import FsActions
from rainmaker.tests import factory_helper

fs = FsActions()

def test_can_scan_single_sync():
    session = init_db()
    sync = factory_helper.Sync()
    session.add(sync)
    session.commit()
    dirs = factory_helper.Dirs(sync.path, 5)
    for d in dirs:
        factory_helper.Files(d, 5)
    scan_manager.scan(session)
    sync_files = session.query(SyncFile).\
        join(Sync).filter(Sync.id==sync.id).all()
    assert len(sync_files) == 30

def test_can_scan_and_discover_files_deleted():
    session = init_db()
    sync = factory_helper.Sync()
    session.add(sync)
    session.commit()
    dirs = factory_helper.Dirs(sync.path, 5)
    for d in dirs:
        factory_helper.Files(d, 5)
    scan_manager.scan(session)
    sync_files = session.query(SyncFile).\
        join(Sync).filter(Sync.id==sync.id,
            SyncFile.does_exist==True).all()
    assert len(sync_files) == 30
    fs.rmdir(dirs[0])
    scan_manager.scan(session)
    sync_files = session.query(SyncFile).\
        join(Sync).filter(Sync.id==sync.id, SyncFile.does_exist==True).all()
    assert len(sync_files) == 24
    
