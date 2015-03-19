import cProfile

import rainmaker
from rainmaker.tests import test_helper
from rainmaker.tests import factory_helper
from rainmaker.db import views
from rainmaker.db.main import init_db, Host, HostFile


def test_can_sync_match(fcount=3000):
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
    cProfile.runctx('views.sync_match(s, lid, hid)', globals(),
            {'s':session,'lid':local.id,'hid':host.id})

if __name__ == '__main__':
    test_can_sync_match(5000)

