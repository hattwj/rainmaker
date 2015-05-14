import rainmaker.tests.factory_helper as fh
from rainmaker.db.main import init_db, SyncFile, Download

from rainmaker.db import observers


def test_download_update_observer():
    host = fh.Host(fh.Sync(1, fake=True), 1)
    hf = fh.HostFile(host, 1, is_dir=False)
    dl = Download()
    dl.from_host_file(hf)

def test_sync_file_update_observer():
    # prep test
    db = init_db()
    sync = fh.Sync(1, fake=True)
    sync_file = fh.SyncFile(sync, 1, fake=True, is_dir=False)
    
    # Save changes
    db.add(sync)
    db.commit()
    
    # Assert no versions
    sync_file = db.query(SyncFile).first()
    assert sync_file.version == 0
    assert len(sync_file.vers) == 0

    # Save (again) with no changes
    db.add(sync_file)
    db.commit()

    # Assert no versions
    sync_file = db.query(SyncFile).first()
    #print('Version:', sync_file.version)
    assert sync_file.version == 0
    assert len(sync_file.vers) == 0

    # Create version by altering serialized attribute of record
    sync_file.file_parts.put(0, 1234, 'test')
    db.add(sync_file)
    db.commit()

    # Assert one version
    sync_file = db.query(SyncFile).first()
    #print('Version:', sync_file.version)
    assert sync_file.version == 1
    assert len(sync_file.vers) == 1
    
    # Assert change saved to file_part
    assert sync_file.file_parts.get(0) == [1234, 'test']

    # Create version by altering attribute of record
    sync_file.file_hash = 'defgh'
    db.add(sync_file)
    #print('Firing 2nd ver commit')
    db.commit()
    #print('Did 2nd ver commit')
    # Assert two versions
    sync_file = db.query(SyncFile).first()
    #print('Version:', sync_file.version)
    assert sync_file.version == 2
    #print('vlen', len(sync_file.vers))
    assert len(sync_file.vers) == 2
