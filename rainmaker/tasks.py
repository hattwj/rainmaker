# Python imports
from __future__ import print_function
import os

from rainmaker.db.main import init_db
from rainmaker.tox.main import init_tox
from rainmaker.sync_manager.main import init_sync

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

def autorun(app):
    log.info("Starting rainmaker version: %s" % app.version)
    log.info('Checking installation...')
    # create user's config dir
    if not os.path.isdir(app.user_dir):
        did_install = True
        app.fs_log.mkdir(app.user_dir) 
        app.fs_log.touch(app.db_path)

    log.info('Initializing db...') 
    app.db = init_db(app.db_path)

    log.info('Configuring Tox...')
    init_tox(app.db)

    log.info('Initializing Sync Managers...')
    init_sync(app)
