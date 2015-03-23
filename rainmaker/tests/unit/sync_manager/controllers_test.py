from rainmaker.sync_manager.controllers import sync_files_controller, file_params
from rainmaker.tests import factory_helper
from rainmaker.db.main import init_db
from rainmaker.net.events import Event, EventHandler

def fail(e):
    assert False

def test_sync_files_controller_lists_files():
    def got_sync_files(event):        
        print(len(event.val()))
        assert event.status == 'ok'
        assert len(event.val()) == 200

    eh = EventHandler(None)
    session = init_db()
    sync = factory_helper.Sync(1, fake=True)
    sync_files = factory_helper.SyncFile(sync, 205, fake=True)
    session.add(sync)
    session.commit()
    sync_files_controller(session, sync, eh)
    eh.call_event('list_sync_files', reply=got_sync_files, error=fail)

def test_sync_files_controller_lists_sync_parts():
    def got_sync_parts(event):
        assert event.status == 'ok'
        assert len(event.val()) == 2
    eh = EventHandler(None)
    session = init_db()
    sync = factory_helper.Sync(1, fake=True)
    sync_file = factory_helper.SyncFile(sync, 1, is_dir=False, 
        file_size=80000, fake=True)
    parts = factory_helper.SyncPart(sync_file)
    session.add(sync)
    session.commit()
    sync_files_controller(session, sync, eh)
    eh.call_event('list_sync_parts', reply=got_sync_parts, error=fail,
        params={'sync_file_id':sync_file.id})

def test_sync_files_controller_gets_file():
    def got_sync_file(event):
        assert event.status == 'ok'
        assert sync_file.to_dict(*file_params) == event.val()
    eh = EventHandler(None)
    session = init_db()
    sync = factory_helper.Sync(1, fake=True)
    sync_file = factory_helper.SyncFile(sync, 1, fake=True)
    session.add(sync)
    session.commit()
    sync_files_controller(session, sync, eh)
    eh.call_event('get_sync_file', reply=got_sync_file, params={'id':1}, error=fail)
