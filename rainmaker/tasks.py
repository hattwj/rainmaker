# Python imports
from __future__ import print_function
import os

from rainmaker.db.main import init_db
from rainmaker.tox.main import init_tox
from rainmaker.sync_manager.main import init_sync

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)


def autorun():
    log.info("Starting rainmaker version: %s" % Application.version)
    log.info('Checking installation...')
    # create user's config dir
    if not os.path.isdir(Application.user_dir):
        did_install = True
        Application.fs_log.mkdir(Application.user_dir) 
        Application.fs_log.touch(Application.db_path)

    log.info('Initializing db...') 
    Application.db = init_db(Application.db_path)

    if Application.start_tox:
        log.info('Configuring Tox...')
        init_tox(Application.db)
    else:
        log.info('Skipping Tox...')

    if Application.start_sync:
        log.info('Initializing Sync Managers...')
        init_sync(Application.db)
    else:
        log.info('Skipping Sync auto start')

def create_sync(path):
    pass
