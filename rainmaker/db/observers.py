import ujson
from sqlalchemy import event


'''
    Observer based actions:
    - Host updated: sync_with_host if ready
    - Download created: start download
'''

from rainmaker.db.main import SyncFile, Download
#from rainmaker.db.serializers import ValidationError

# 
def _on_sync_file_save(mapper, connection, target):
    '''
        listen for the 'save' events"
    '''
    print('observer;;', target)
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    if target.id is not None:
        target.vers.add(target.before_changes())
        target.version += 1
        target.ver_data = target.vers.dump()

# 
print('Yup')
event.listens_for(SyncFile, 'before_update', _on_sync_file_save)
event.listens_for(SyncFile, 'before_insert', _on_sync_file_save)

# 
def _on_download_save(mapper, connection, target):
    "listen for the 'before_update' event"
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    if target.needed_parts.changed:
        target.nparts = target.needed_parts.dump()

# load listeners
event.listens_for(Download, 'before_update', _on_download_save)
event.listens_for(Download, 'before_insert', _on_download_save)


