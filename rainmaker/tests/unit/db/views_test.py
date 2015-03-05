from rainmaker.tests import test_helper
from rainmaker.tests import factory_helper
from rainmaker.db import views
from rainmaker.db.main import init_db, Host

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


