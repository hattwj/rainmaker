import ujson
from sqlalchemy import event

from rainmaker.db.main import SyncFile, Download
from rainmaker.db.serializers import ValidationError

# standard decorator style
@event.listens_for(SyncFile, 'before_update')
def receive_before_update(mapper, connection, target):
    "listen for the 'before_update' event"
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    target.version += 1
    data = [target.before_changes()]
    if target.ver_data is not None:
        data.append(ujson.dumps(target.ver_data))
    target.ver_data = ujson.dumps(data)

# standard decorator style
@event.listens_for(Download, 'before_update')
def receive_before_update(mapper, connection, target):
    "listen for the 'before_update' event"
    if target.file_parts.changed:
        target.fparts = target.file_parts.dump()
    if target.needed_parts.changed:
        target.nparts = target.needed_parts.dump()
