from time import sleep
from rainmaker.db.main import init_db, Sync, SyncFile
from rainmaker.file_system import FsActions
from rainmaker.sync_manager import fs_manager
from rainmaker.tests import factory_helper

fs = FsActions()

def test_can_watch_single_sync():
    session = init_db()
    sync = factory_helper.Sync()
    session.add(sync)
    session.commit()
    fs_manager.init()
    watch = fs_manager.SyncWatch(session, sync)
    sleep(0.5)
    dirs = factory_helper.Dirs(sync.path, 2)
    for d in dirs:
        sleep(0.5)
        factory_helper.Files(d, 1)    
    fs.rmdir(dirs[0])
    sleep(0.5)
    watch.commit()
    sync_files = session.query(SyncFile).filter(SyncFile.sync_id == sync.id,
        SyncFile.does_exist == False).all()
    fs_manager.stop()
