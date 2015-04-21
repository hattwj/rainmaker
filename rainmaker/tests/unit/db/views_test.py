from rainmaker.tests import test_helper
from rainmaker.tests import factory_helper
from rainmaker.db import views
from rainmaker.db.main import init_db, Host, HostFile

def test_can_diff_empty():
    session = init_db()
    local= factory_helper.Sync()
    host = Host(pubkey='')
    local.hosts.append(host)
    session.add(local)
    session.commit()
    l_files, r_files = views.sync_diff(session, local.id, host.id)
    assert len(l_files) == 0
    assert len(r_files) == 0

def test_can_diff_local():
    session = init_db()
    local= factory_helper.Sync()
    files = factory_helper.SyncFile(local, 5, does_exist=True)
    local.sync_files += files
    host = Host(pubkey='')
    local.hosts.append(host)
    session.add(local)
    session.commit()
    l_files, r_files = views.sync_diff(session, local.id, host.id)
    assert len(l_files) == 5
    assert len(r_files) == 0

def test_can_diff_remote():
    session = init_db()
    local= factory_helper.Sync()
    host = Host(pubkey='')
    local.hosts.append(host)
    host.host_files += factory_helper.HostFile(host, 5)
    session.add(local)
    session.commit()
    l_files, r_files = views.sync_diff(session, local.id, host.id)
    assert len(l_files) == 0
    assert len(r_files) == 5

def test_can_diff_both():
    session = init_db()
    local= factory_helper.Sync()
    files = factory_helper.SyncFile(local, 5, does_exist=True)
    local.sync_files += files
    host = Host(pubkey='aaa')
    local.hosts.append(host)
    host.host_files += factory_helper.HostFile(host, 5)
    session.add(local)
    session.commit()
    l_files, r_files = views.sync_diff(session, local.id, host.id)
    assert len(l_files) == 5
    assert len(r_files) == 5

def test_can_diff_repeat():
    session = init_db()
    local= factory_helper.Sync()
    files = factory_helper.SyncFile(local, 5, does_exist=True)
    files[0].does_exist = False
    local.sync_files += files
    host = Host(pubkey='')
    local.hosts.append(host)
    host.host_files += factory_helper.HostFile(host, 5)
    host.host_files[0].does_exist = False
    session.add(local)
    session.commit()
    l_files, r_files = views.sync_diff(session, local.id, host.id)
    assert len(l_files) == 5
    assert len(r_files) == 5
    new_files = [f.to_sync_file(local.id) for f in r_files]
    local.sync_files += new_files
    session.add(local)
    session.commit()
    l_files, r_files = views.sync_diff(session, local.id, host.id)
    assert len(l_files) == 5
    assert len(r_files) == 0


def test_can_sync_match(fcount=50):
    session = init_db()
    local= factory_helper.Sync() 
    files = factory_helper.SyncFile(local, fcount, does_exist=True, fake=True)
    host = Host(sync=local, pubkey='')
    session.add(local)
    session.add(host)
    session.commit()
    for f in files:
        hf = f.to_host_file()
        host.host_files.append(hf)
    session.add(host)
    session.commit()
    views.sync_match(session, local.id, host.id)
    host_files = session.query(HostFile).all()
    assert len(host_files) == fcount
    for f in host_files:
        assert f.cmp_id is not None
        assert f.cmp_ver is not None

def test_find_last_changed():
    db = init_db()
    result = views.find_last_changed(db, 1, 1)
    assert result == (0, 0)
    sync = factory_helper.SyncRand()
    db.add(sync)
    db.commit()
    result = views.find_last_changed(db, 1, 1)
    assert result[0] > 0
    assert result[1] > 0

