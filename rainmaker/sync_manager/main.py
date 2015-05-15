from rainmaker.db.main import Sync
from rainmaker.sync_manager.scan_manager import scan

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

def init_sync(app):
    scan(app.db)

