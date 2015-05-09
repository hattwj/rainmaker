import ujson
from sqlalchemy import event

from rainmaker.db.main import SyncFile, Download
#from rainmaker.db.serializers import ValidationError

# standard decorator style
@event.listens_for(SyncFile, 'before_update')
def _on_sync_file_update(mapper, connection, target):
    '''
        listen for the 'before_update' event"
    '''
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    target.vers.add(target.before_changes())
    target.version += 1
    target.ver_data = target.vers.dump()

# standard decorator style
@event.listens_for(Download, 'before_update')
def _on_download_update(mapper, connection, target):
    "listen for the 'before_update' event"
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    if target.needed_parts.changed:
        target.nparts = target.needed_parts.dump()
