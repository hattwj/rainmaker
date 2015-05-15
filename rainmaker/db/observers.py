import ujson
from sqlalchemy import event


'''
    Observer based actions:
    - Host updated: sync_with_host if ready
    - Download created: start download
'''

from rainmaker.db.main import SyncFile, Download

#
@event.listens_for(SyncFile, 'before_update')
@event.listens_for(SyncFile, 'before_insert')
def _on_sync_file_save(mapper, connection, target):
    '''
        listen for save events
    '''
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    if target.id is not None:
        target.vers.add(target.before_changes())
        target.version += 1
        target.ver_data = target.vers.dump()

# 
@event.listens_for(Download, 'before_update')
@event.listens_for(Download, 'before_insert')
def _on_download_save(mapper, connection, target):
    '''
        listen for save events
    '''
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    if target.needed_parts.changed:
        target.nparts = target.needed_parts.dump()



